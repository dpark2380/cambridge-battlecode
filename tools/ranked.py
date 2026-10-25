#!/usr/bin/env python3
"""Download our ranked matches from the platform and summarise them (needs `cambc login`, cambc >= 3).

    python3 tools/ranked.py replays/daniel-v8                  # newest 100 ranked matches
    python3 tools/ranked.py replays/daniel-v8 --since 2026-10-21T00:00 --team "Deer Park"
    python3 tools/ranked.py replays/daniel-v8 --limit 1000 --replays losses   # also analyse every loss

Writes <dir>/matches.json (platform listing) and <dir>/summaries/<match id>.json (the same schema as
`cambc run --statistics --json`), skipping summaries already downloaded (stripped of the per-round timelines), then prints the record, averages
for wins and losses, and every game per map as `ours:theirs@round d<our deaths>/<their deaths>`.
"""
import argparse
import collections
import json
import subprocess
import time
from pathlib import Path

import arena

ROOT = Path(__file__).resolve().parent.parent


def cambc(*args):
    return subprocess.run([arena.CAMBC, *args], capture_output=True, text=True)


def list_matches(limit, since=""):
    """Newest-first finished ranked matches, following the listing's cursor (the platform caps a page at 100)."""
    matches, cursor = [], None
    while len(matches) < limit:
        args = ["matches", "list", "--team", "me", "--kind", "ranked", "--limit", str(min(100, limit - len(matches))), "--json"]
        out = cambc(*args, *(["--cursor", cursor] if cursor else []))
        if out.returncode:
            raise SystemExit(out.stderr)
        page = json.loads(out.stdout)
        matches += page["matches"]
        cursor = page.get("nextCursor")
        if not cursor or not page["matches"] or page["matches"][-1]["createdAt"] < since:
            break
    return [m for m in matches if m["status"] == "finished" and m["finishedAt"] >= since]


def download(match_id, path, *kind):
    """kind = ("summary", "--json") for the summary, () for the replay zip."""
    for _ in range(5):  # the platform rate-limits bursts (HTTP 429)
        if path.exists() or cambc("matches", *(kind or ("download",)), match_id, "-o", str(path)).returncode == 0:
            return
        time.sleep(3)


def compact(path):
    """Drop the per-round timelines and event log (~95% of a summary, read by no tool)."""
    s = json.loads(path.read_text())
    if "events" in s or "championTimelines" in s:
        path.write_text(json.dumps({k: v for k, v in s.items() if k not in ("events", "championTimelines")}))


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
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--replays", choices=("none", "losses", "all"), default="none",
                        help="also download replays, analyse each into <dir>/analysis/<match id>.txt, then delete the replay")
    args = parser.parse_args()

    out = Path(args.dir)
    (out / "summaries").mkdir(parents=True, exist_ok=True)
    (out / "analysis").mkdir(exist_ok=True)
    matches = list_matches(args.limit, args.since)
    (out / "matches.json").write_text(json.dumps(matches, indent=1))

    per_map, sums = collections.defaultdict(list), collections.defaultdict(collections.Counter)
    for m in matches:
        path = out / "summaries" / f"{m['matchId']}.json"
        download(m["matchId"], path, "summary", "--json")
        us = next(t for t in m["teams"] if t["name"] == args.team)
        if (args.replays == "all" or (args.replays == "losses" and us["result"] != "win")) \
                and not (out / "analysis" / f"{m['matchId']}.txt").exists():
            download(m["matchId"], out / "analysis" / f"{m['matchId']}.zip")
            if (out / "analysis" / f"{m['matchId']}.zip").exists():
                analyze(out / "analysis" / f"{m['matchId']}.zip", out / "analysis")
        if not path.exists():
            print("missing", m["matchId"])
            continue
        compact(path)
        s = json.loads(path.read_text())
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
