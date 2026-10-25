#!/usr/bin/env python3
"""Tally what the top ladder teams draft and build (read-only platform calls; needs `cambc login`).

    python3 tools/scout.py --top 20 --matches 100 --summaries 10      # writes data/scout/<time>.json + prints

For each of the top --top teams: its last --matches ranked games from `cambc matches list --team <id>` (drafts,
results, maps), and --summaries of them from `cambc matches summary` (items bought per champion). Prints
how often each champion is drafted (overall and as first pick) and the average shards bought per champion, by stat.
"""
import argparse
import collections
import json
import subprocess
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import arena

ROOT = arena.ROOT
# champion_draft order in sdk/cpp/cambc.h: the ids the match listing reports.
DRAFT = ["ryth", "vesper_vale", "vendetta", "cassi_and_issac", "stellar", "prism", "marcella", "willow", "ren",
         "varg", "tavi", "heart_of_ruin"]


def cambc(*args):
    out = subprocess.run([arena.CAMBC, *args], capture_output=True, text=True)
    return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None


def builds(match_id, team_side):
    """{champion name: Counter(item -> quantity bought)} for one side of a match."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "s.json"
        for attempt in range(3):
            if subprocess.run([arena.CAMBC, "matches", "summary", match_id, "--json", "-o", str(path)],
                              capture_output=True).returncode == 0:
                break
            time.sleep(3 * (attempt + 1))
        else:
            return {}
        s = json.loads(path.read_text())
    return {c["name"]: collections.Counter({i["item"]: int(i["quantity"]) for i in c.get("itemsBought", [])})
            for c in s["champions"] if c["team"] == team_side}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--matches", type=int, default=100)
    parser.add_argument("--summaries", type=int, default=10)
    parser.add_argument("--jobs", type=int, default=8)
    args = parser.parse_args()

    teams = cambc("ladder", "--limit", str(args.top), "--json")["teams"][:args.top]
    report = []
    for t in teams:
        listing = cambc("matches", "list", "--team", t["teamId"], "--kind", "ranked", "--limit", str(args.matches), "--json")
        games = [m for m in (listing or {}).get("matches", []) if m["status"] == "finished"]
        rows = []
        for m in games:
            us = next(x for x in m["teams"] if x["teamId"] == t["teamId"])
            rows.append({"match": m["matchId"], "map": m["map"], "side": us["side"], "win": us["result"] == "win",
                         "picks": [DRAFT[int(c)] for c in us["characters"]]})
        report.append({"rank": t["rank"], "name": t["name"], "rating": t["rating"], "games": rows})

    # Builds from a sample of each team's games, fetched in parallel.
    jobs = [(entry, row) for entry in report for row in entry["games"][:args.summaries]]
    with ThreadPoolExecutor(args.jobs) as pool:
        for (entry, row), b in zip(jobs, pool.map(lambda j: builds(j[1]["match"], "team" + j[1]["side"].upper()), jobs)):
            row["builds"] = {k: dict(v) for k, v in b.items()}

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
