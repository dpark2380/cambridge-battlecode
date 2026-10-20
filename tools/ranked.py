#!/usr/bin/env python3
"""Download our ranked matches from the platform and summarise them (needs `cambc login`, cambc >= 3).

    python3 tools/ranked.py replays/daniel-v8                  # newest 100 ranked matches
    python3 tools/ranked.py replays/daniel-v8 --since 2026-10-21T00:00 --team "Deer Park"

Writes <dir>/matches.json (platform listing) and <dir>/summaries/<match id>.json (the same schema as
`cambc run --statistics --json`), skipping summaries already downloaded, then prints the record, averages
for wins and losses, and every game per map as `ours:theirs@round d<our deaths>/<their deaths>`.
"""
import argparse
import collections
import json
import subprocess
import time
from pathlib import Path

import arena


def cambc(*args):
    return subprocess.run([arena.CAMBC, *args], capture_output=True, text=True)


def list_matches(limit):
    out = cambc("matches", "list", "--team", "me", "--kind", "ranked", "--limit", str(limit), "--json")
    if out.returncode:
        raise SystemExit(out.stderr)
    return [m for m in json.loads(out.stdout)["matches"] if m["status"] == "finished"]


def download(match_id, path):
    for _ in range(5):  # the platform rate-limits bursts (HTTP 429)
        if path.exists() or cambc("matches", "summary", match_id, "--json", "-o", str(path)).returncode == 0:
            return
        time.sleep(3)


def total(summary, team, metric):
    return sum(float(c["metrics"][metric]) for c in summary["champions"] if c["team"] == team)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dir")
    parser.add_argument("--team", default="Deer Park", help="our team name on the platform")
    parser.add_argument("--since", default="", help="only matches finished at or after this ISO time")
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()

    out = Path(args.dir)
    (out / "summaries").mkdir(parents=True, exist_ok=True)
    matches = [m for m in list_matches(args.limit) if m["finishedAt"] >= args.since]
    (out / "matches.json").write_text(json.dumps(matches, indent=1))

    per_map, sums = collections.defaultdict(list), collections.defaultdict(collections.Counter)
    for m in matches:
        path = out / "summaries" / f"{m['matchId']}.json"
        download(m["matchId"], path)
        if not path.exists():
            print("missing", m["matchId"])
            continue
        s = json.loads(path.read_text())
        us = next(t for t in m["teams"] if t["name"] == args.team)
        ours = "team" + us["side"].upper()
        theirs = "teamB" if ours == "teamA" else "teamA"
        gems = {t["team"]: int(t["submittedGems"]) for t in s["teams"]}
        row = {"us": gems[ours], "them": gems[theirs], "round": s["match"]["roundsCompleted"],
               **{f"{k}": total(s, ours, k) for k in ("deaths", "kills", "earnedGold")},
               **{f"their_{k}": total(s, theirs, k) for k in ("deaths", "kills", "earnedGold")}}
        won = us["result"] == "win"
        per_map[m["map"]].append((won, row))
        sums["W" if won else "L"].update(row | {"games": 1})

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


if __name__ == "__main__":
    main()
