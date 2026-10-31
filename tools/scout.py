#!/usr/bin/env python3
"""Tally what the top ladder teams draft and build (read-only platform calls; needs `cambc login`).

    python3 tools/scout.py --top 20 --matches 100 --summaries 10      # writes data/scout/<time>.json + prints
    python3 tools/scout.py --top 20 --matches 30 --summaries 0 --replays 3 --maps 00stampede,01corridors

With --replays N, also downloads each team's N newest games (on --maps first, if given) and decodes them with
tools/replay/analyze.mjs into data/scout/replays/<match id>.txt (report) + .stats.json + .timeline.csv.gz
(per-round positions, gems, K/D), then deletes the replay. Games already decoded are skipped, so re-runs are cheap.
In the report, "us" is team A, whoever that is: check the team names in data/scout/replays/<match id>.json.

For each of the top --top teams: its last --matches ranked games from `cambc matches list --team <id>` (drafts,
results, maps), and --summaries of them from `cambc matches summary` (items bought per champion, and a feature row
per game appended to data/scout/features.jsonl for tools/benchmark.py). Prints
how often each champion is drafted (overall and as first pick) and the average shards bought per champion, by stat.
"""
import argparse
import collections
import gzip
import json
import shutil
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import arena
import features

ROOT = arena.ROOT
# champion_draft order in sdk/cpp/cambc.h: the ids the match listing reports.
DRAFT = ["ryth", "vesper_vale", "vendetta", "cassi_and_issac", "stellar", "prism", "marcella", "willow", "ren",
         "varg", "tavi", "heart_of_ruin"]


def cambc(*args):
    out = subprocess.run([arena.CAMBC, *args], capture_output=True, text=True)
    return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None


def builds(match_id, team_side, row_info):
    """({champion name: Counter(item -> quantity bought)}, feature row) for one side of a match."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "s.json"
        for attempt in range(3):
            if subprocess.run([arena.CAMBC, "matches", "summary", match_id, "--json", "-o", str(path)],
                              capture_output=True).returncode == 0:
                break
            time.sleep(3 * (attempt + 1))
        else:
            return {}, None
        s = json.loads(path.read_text())
        keep = ROOT / "data" / "scout" / "summaries" / f"{match_id}.json.gz"  # full summary for tools/winmodel.py
        keep.parent.mkdir(parents=True, exist_ok=True)
        if not keep.exists():
            with gzip.open(keep, "wt", compresslevel=9) as f:
                f.write(path.read_text())
    items = {c["name"]: collections.Counter({i["item"]: int(i["quantity"]) for i in c.get("itemsBought", [])})
             for c in s["champions"] if c["team"] == team_side}
    row = features.row(s, team_side, match_id, row_info["map"], row_info["win"]) | {"team": row_info["team"],
                                                                                    "rank": row_info["rank"]}
    return items, row


def decode(match, out):
    """Download one replay, decode it into out/<id>.txt/.stats.json/.timeline.csv.gz, delete the zip."""
    mid = match["match"]
    if (out / f"{mid}.txt").exists():
        return
    zip_path = out / f"{mid}.zip"
    for attempt in range(3):
        if subprocess.run([arena.CAMBC, "matches", "download", mid, "-o", str(zip_path)], capture_output=True).returncode == 0:
            break
        time.sleep(3 * (attempt + 1))
    else:
        return
    report = subprocess.run(["node", str(ROOT / "tools/replay/analyze.mjs"), "--us", "A", "--out", str(out), str(zip_path)],
                            capture_output=True, text=True)
    zip_path.unlink(missing_ok=True)
    if report.returncode:
        return
    csv = out / f"{mid}.timeline.csv"
    if csv.exists():
        with csv.open("rb") as src, gzip.open(f"{csv}.gz", "wb") as dst:
            shutil.copyfileobj(src, dst)
        csv.unlink()
    (out / f"{mid}.json").write_text(json.dumps(match))
    (out / f"{mid}.txt").write_text(report.stdout)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--matches", type=int, default=100)
    parser.add_argument("--summaries", type=int, default=10)
    parser.add_argument("--replays", type=int, default=0, help="replays per team to download and decode")
    parser.add_argument("--maps", default="", help="comma-separated maps to prefer for --replays (listing names, e.g. 00stampede)")
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()

    teams = []  # `cambc ladder` returns at most 100 teams per page
    for page in range(1, (args.top + 99) // 100 + 1):
        teams += cambc("ladder", "--page", str(page), "--limit", "100", "--json")["teams"]
    teams = teams[:args.top]
    report = []
    for t in teams:
        listing = cambc("matches", "list", "--team", t["teamId"], "--kind", "ranked", "--limit", str(args.matches), "--json")
        games = [m for m in (listing or {}).get("matches", []) if m["status"] == "finished"]
        rows = []
        for m in games:
            us = next(x for x in m["teams"] if x["teamId"] == t["teamId"])
            them = next(x for x in m["teams"] if x["teamId"] != t["teamId"])
            rows.append({"match": m["matchId"], "map": m["map"], "side": us["side"], "win": us["result"] == "win",
                         "picks": [DRAFT[int(c)] for c in us["characters"]], "team": t["name"], "rank": t["rank"],
                         "opponent": them["name"], "finished": m["finishedAt"]})
        report.append({"rank": t["rank"], "name": t["name"], "rating": t["rating"], "games": rows})

    # Builds from a sample of each team's games, fetched in parallel.
    jobs = [(entry, row) for entry in report for row in entry["games"][:args.summaries]]
    rows_path = ROOT / "data" / "scout" / "features.jsonl"
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    known = {json.loads(line)["match"] + json.loads(line)["side"] for line in rows_path.open()} if rows_path.exists() else set()
    with ThreadPoolExecutor(args.jobs) as pool, rows_path.open("a") as rows_out:
        for (entry, row), (b, feat) in zip(jobs, pool.map(
                lambda j: builds(j[1]["match"], "team" + j[1]["side"].upper(), j[1]), jobs)):
            row["builds"] = {k: dict(v) for k, v in b.items()}
            if feat and feat["match"] + feat["side"] not in known:
                rows_out.write(json.dumps(feat) + "\n")  # data/scout/features.jsonl: top-team benchmark rows

    if args.replays:
        prefer = set(filter(None, args.maps.split(",")))
        chosen = []
        for entry in report:
            # Newest games on the preferred maps, else the newest games (the listing is newest first).
            chosen += [g for g in entry["games"] if g["map"] in prefer][:args.replays] or entry["games"][:args.replays]
        replay_dir = ROOT / "data" / "scout" / "replays"
        replay_dir.mkdir(parents=True, exist_ok=True)
        with ThreadPoolExecutor(args.jobs) as pool:
            list(pool.map(lambda g: decode(g, replay_dir), chosen))
        done = sum((replay_dir / (g["match"] + ".txt")).exists() for g in chosen)
        print(f"decoded {done}/{len(chosen)} replays into {replay_dir.relative_to(ROOT)}")

    out = ROOT / "data" / "scout" / f"{time.strftime('%Y%m%dT%H%MZ', time.gmtime())}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report))

    picked, first, wins = collections.Counter(), collections.Counter(), collections.Counter()
    shards = collections.defaultdict(collections.Counter)
    seen = collections.Counter()
    for entry in report:
        w = sum(g["win"] for g in entry["games"])
        print(f"#{entry['rank']:<3} {entry['name'][:28]:28s} {entry['rating']:6.0f}  {w}-{len(entry['games']) - w}  "
              + ", ".join(f"{c} {n}" for c, n in collections.Counter(p for g in entry["games"] for p in g["picks"]).most_common(6)))
        for g in entry["games"]:
            picked.update(set(g["picks"]))
            first[g["picks"][0]] += 1
            wins.update({p: g["win"] for p in set(g["picks"])})
            for champ, items in g.get("builds", {}).items():
                seen[champ] += 1
                shards[champ].update(items)
    total = sum(len(e["games"]) for e in report)
    print(f"\nover {total} games of the top {len(report)}: champion, drafted %, first-pick %, win % when drafted")
    for c, n in picked.most_common():
        print(f"  {c:16s} {100 * n / total:5.1f}%  {100 * first[c] / total:5.1f}%  {100 * wins[c] / n:5.1f}%")
    print("\naverage items bought per game (shards; emblems are counted inside their shards)")
    for champ, items in sorted(shards.items()):
        top = [(i, q / seen[champ]) for i, q in items.most_common() if "Shard" in i][:6]
        print(f"  {champ:12s} n={seen[champ]:3d}  " + ", ".join(f"{i.replace(' Shard of ', ':')} {q:.1f}" for i, q in top))
    print(f"\nsaved {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
