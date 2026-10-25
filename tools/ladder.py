#!/usr/bin/env python3
"""Track our ladder rating and which submission is live (T4; needs `cambc login`).

    python3 tools/ladder.py snapshot                 # save the ladder, append our rank/rating to docs/ladder_history.csv
    python3 tools/ladder.py submitted bots/daniel/v9 --time 2026-10-25T10:16Z --platform-version 8 --note "..."
    python3 tools/ladder.py versions                 # rating at the start and end of each submission's window

Ranked listings do not say which submission played, so docs/submissions.jsonl records each submission's time;
a version's games are those between its submission and the next. Record every `cambc submit` here.
Full snapshots go to data/ladder/<time>.json (gitignored); docs/ladder_history.csv (in git) holds our row.
"""
import argparse
import csv
import json
import subprocess
import time
from pathlib import Path

import arena

ROOT = arena.ROOT
HISTORY = ROOT / "docs" / "ladder_history.csv"
SUBMISSIONS = ROOT / "docs" / "submissions.jsonl"
TEAM = "Deer Park"


def ladder():
    teams, page = [], 1
    while True:
        for attempt in range(6):  # the public API rate-limits bursts (HTTP 429)
            out = subprocess.run([arena.CAMBC, "ladder", "--page", str(page), "--limit", "25", "--json"],
                                 capture_output=True, text=True)
            if out.returncode == 0 or "429" not in out.stderr:
                break
            time.sleep(10 * (attempt + 1))
        if out.returncode:
            raise SystemExit(out.stderr)
        rows = json.loads(out.stdout)["teams"]
        teams += rows
        if len(rows) < 25:
            return teams
        page += 1


def snapshot():
    now = time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime())
    teams = ladder()
    path = ROOT / "data" / "ladder" / f"{now}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"time": now, "teams": teams}))
    us = next(t for t in teams if t["name"] == TEAM)
    new = not HISTORY.exists()
    with HISTORY.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "rank", "rating", "matches", "teams"])
        w.writerow([now, us["rank"], round(us["rating"], 1), us["matches"], len(teams)])
    print(f"{now}: #{us['rank']} of {len(teams)}, rating {us['rating']:.0f}, {us['matches']} matches")


def versions():
    subs = [json.loads(line) for line in SUBMISSIONS.read_text().splitlines() if line.strip()]
    history = list(csv.DictReader(HISTORY.open())) if HISTORY.exists() else []
    for i, s in enumerate(subs):
        end = subs[i + 1]["time"] if i + 1 < len(subs) else "9999"
        window = [h for h in history if s["time"] <= h["time"] < end]
        span = f"rating {window[0]['rating']} -> {window[-1]['rating']}, rank #{window[0]['rank']} -> #{window[-1]['rank']}" \
            if window else "no snapshots"
        print(f"{s['time']}  {s['bot']:18s} (platform v{s.get('platform_version', '?')}): {span}  {s.get('note', '')}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("snapshot")
    sub.add_parser("versions")
    p = sub.add_parser("submitted")
    p.add_argument("bot")
    p.add_argument("--time", default=time.strftime("%Y-%m-%dT%H:%MZ", time.gmtime()))
    p.add_argument("--platform-version", type=int)
    p.add_argument("--note", default="")
    args = parser.parse_args()
    if args.cmd == "snapshot":
        snapshot()
    elif args.cmd == "versions":
        versions()
    else:
        with SUBMISSIONS.open("a") as f:
            f.write(json.dumps({"time": args.time, "bot": args.bot, "platform_version": args.platform_version,
                                "note": args.note}) + "\n")
        print(f"recorded {args.bot} at {args.time}")


if __name__ == "__main__":
    main()
