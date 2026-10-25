#!/usr/bin/env python3
"""Download our ranked matches from the platform and summarise them (needs `cambc login`, cambc >= 3).

    python3 tools/ranked.py replays/daniel-v9 --since 2026-10-25T11:00 --replays losses   # usual pull
    python3 tools/ranked.py replays/daniel-v8 --limit 1000 --team "Deer Park"

Incremental: <dir>/matches.json accumulates every match seen, and listing stops at the first page that is
all known (or older than --since, or after --limit new matches), so a re-run only fetches what is new.
Summaries go to <dir>/summaries/<match id>.json.gz: full (`cambc run --statistics --json` schema with the `events`
log and per-round timelines), gzipped to ~70 kB. Summaries saved before 2026-10-25 23:30 are stripped .json files.
Every game also gets a feature row in <dir>/features.jsonl (tools/features.py: deaths by killer, camp clears,
fuel exhaustion, shards bought, gems at rounds 250/500/1000, loss signatures). With --replays, each selected replay is analysed into <dir>/analysis/<match id>.txt
(+ .stats.json) and deleted. Downloads run --jobs at a time (measured: one summary ~2 s, one replay ~8 s,
8 in parallel take no longer than one, no rate limiting). Then prints the record over every stored match
since --since, averages for wins and losses, every game per map as `ours:theirs@round d<ours>/<theirs>`, and a
table of loss signatures per map.
"""
import argparse
import collections
import gzip
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import arena
import features

ROOT = Path(__file__).resolve().parent.parent


def cambc(*args):
    return subprocess.run([arena.CAMBC, *args], capture_output=True, text=True)


def list_matches(limit, since, known):
    """New finished ranked matches, newest first, following the listing's cursor (pages hold at most 100).
    Stops at a page with nothing new, one reaching back before `since`, or `limit` new matches."""
    new, cursor = [], None
    while len(new) < limit:
        out = cambc("matches", "list", "--team", "me", "--kind", "ranked", "--limit", "100", "--json",
                    *(["--cursor", cursor] if cursor else []))
        if out.returncode:
            raise SystemExit(out.stderr)
        page = json.loads(out.stdout)
        fresh = [m for m in page["matches"] if m["status"] == "finished" and m["finishedAt"] >= since
                 and m["matchId"] not in known]
        new += fresh[:limit - len(new)]
        cursor = page.get("nextCursor")
        if not cursor or not fresh or page["matches"][-1]["createdAt"] < since:
            break
    return new


def download(match_id, path, *kind):
    """kind = ("summary", "--json") for the summary, () for the replay zip. True once the file exists."""
    for attempt in range(5):  # retry transient failures (HTTP 429 or 5xx) with backoff
        if path.exists() or cambc("matches", *(kind or ("download",)), match_id, "-o", str(path)).returncode == 0:
            return True
        time.sleep(3 * (attempt + 1))
    return False


def summary_path(out, match_id):
    """The stored summary: full and gzipped, or stripped .json from before the switch."""
    full = out / "summaries" / f"{match_id}.json.gz"
    return full if full.exists() else out / "summaries" / f"{match_id}.json"


def save_gzipped(path):
    """Gzip a downloaded summary next to itself (path + .gz) and delete the plain copy."""
    with path.open("rb") as src, gzip.open(f"{path}.gz", "wb", compresslevel=9) as dst:
        dst.write(src.read())
    path.unlink()


def analyze(zip_path, out):
    """Decode a replay into <out>/<match id>.txt (the analyze.mjs report) and .stats.json, then delete the zip
    and the bulky timeline CSV: replays are 0.1-1 MB each and only needed once."""
    report = subprocess.run(["node", str(ROOT / "tools/replay/analyze.mjs"), "--out", str(out), str(zip_path)],
                            capture_output=True, text=True)
    if report.returncode:
        print("analyze failed", zip_path.name, report.stderr.strip()[-300:])
        return
    (out / f"{zip_path.stem}.txt").write_text(report.stdout)
    (out / f"{zip_path.stem}.timeline.csv").unlink(missing_ok=True)
    zip_path.unlink()


def total(summary, team, metric):
    return sum(float(c["metrics"][metric]) for c in summary["champions"] if c["team"] == team)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dir")
    parser.add_argument("--team", default="Deer Park", help="our team name on the platform")
    parser.add_argument("--since", default="", help="only matches finished at or after this ISO time")
    parser.add_argument("--limit", type=int, default=500, help="most new matches to fetch this run")
    parser.add_argument("--jobs", type=int, default=8, help="parallel downloads")
    parser.add_argument("--replays", choices=("none", "losses", "all"), default="none",
                        help="also download replays, analyse each into <dir>/analysis/<match id>.txt, then delete the replay")
    args = parser.parse_args()

    out = Path(args.dir)
    (out / "summaries").mkdir(parents=True, exist_ok=True)
    (out / "analysis").mkdir(exist_ok=True)
    listing = out / "matches.json"
    stored = {m["matchId"]: m for m in json.loads(listing.read_text())} if listing.exists() else {}
    new = list_matches(args.limit, args.since, stored)
    stored.update({m["matchId"]: m for m in new})
    listing.write_text(json.dumps(sorted(stored.values(), key=lambda m: m["finishedAt"], reverse=True), indent=1))
    matches = [m for m in stored.values() if m["finishedAt"] >= args.since]
    ours_of = lambda m: next(t for t in m["teams"] if t["name"] == args.team)

    def fetch_summary(m):
        path = out / "summaries" / f"{m['matchId']}.json"
        if download(m["matchId"], path, "summary", "--json"):
            save_gzipped(path)

    def fetch_replay(m):
        report, zip_path = out / "analysis" / f"{m['matchId']}.txt", out / "analysis" / f"{m['matchId']}.zip"
        if not report.exists() and download(m["matchId"], zip_path):
            analyze(zip_path, out / "analysis")

    wanted = [m for m in matches if args.replays == "all" or (args.replays == "losses" and ours_of(m)["result"] != "win")]
    todo = [m for m in matches if not summary_path(out, m["matchId"]).exists()]
    todo_replays = [m for m in wanted if not (out / "analysis" / f"{m['matchId']}.txt").exists()]
    print(f"{len(new)} new matches; fetching {len(todo)} summaries and {len(todo_replays)} replays", flush=True)
    started = time.time()
    with ThreadPoolExecutor(args.jobs) as pool:
        list(pool.map(fetch_summary, todo))
        list(pool.map(fetch_replay, todo_replays))
    print(f"downloaded in {time.time() - started:.0f}s", flush=True)

    per_map, sums = collections.defaultdict(list), collections.defaultdict(collections.Counter)
    rows = []
    for m in matches:
        path = summary_path(out, m["matchId"])
        if not path.exists():
            print("missing", m["matchId"])
            continue
        us = ours_of(m)
        s = features.load(path)
        ours = "team" + us["side"].upper()
        theirs = "teamB" if ours == "teamA" else "teamA"
        won = us["result"] == "win"
        rows.append(features.row(s, ours, m["matchId"], m["map"], won))
        gems = {t["team"]: int(t["submittedGems"]) for t in s["teams"]}
        row = {"us": gems[ours], "them": gems[theirs], "round": s["match"]["roundsCompleted"],
               **{f"{k}": total(s, ours, k) for k in ("deaths", "kills", "earnedGold")},
               **{f"their_{k}": total(s, theirs, k) for k in ("deaths", "kills", "earnedGold")}}
        per_map[m["map"]].append((won, row))
        sums["W" if won else "L"].update(row | {"games": 1})
    (out / "features.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))

    wins = len([1 for games in per_map.values() for won, _ in games if won])
    print(f"{wins}-{sum(map(len, per_map.values())) - wins} over {len(matches)} ranked matches")
    for key, label in (("W", "wins"), ("L", "losses")):
        n = sums[key]["games"]
        if n:
            print(f"{label:6s} " + " ".join(f"{k}={v / n:.0f}" for k, v in sums[key].items() if k != "games"))
    for name, games in sorted(per_map.items()):
        w = sum(won for won, _ in games)
        print(f"{name:22s} {w}-{len(games) - w}  " + "  ".join(
            f"{r['us']}:{r['them']}@{r['round']} d{r['deaths']:.0f}/{r['their_deaths']:.0f}" for _, r in games))
    print("\nloss signatures (tools/features.py):")
    print(features.table(rows))


if __name__ == "__main__":
    main()
