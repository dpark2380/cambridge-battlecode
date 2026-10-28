#!/usr/bin/env python3
"""Unranked scrims (T9; `cambc match-groups`, needs `cambc login`).

A fixed panel of opponents and maps is played against every submitted version. Ranked matchmaking changes
the opponents as our rating moves, which hid whether v19 or the ladder caused its 16-24 (B58); the panel does not.

    python3 tools/scrim.py panel           # queue the panel for the live bot (skips groups it already has)
    python3 tools/scrim.py create <team id> --maps a,b,c,d,e [--sides a,b,a,b,a]   # one extra group
    python3 tools/scrim.py sync            # download finished groups: summaries, feature rows, replay reports
    python3 tools/scrim.py report          # W-L per version, opponent and map, plus feature means
    python3 tools/scrim.py quota

Scrims always play our *submitted* bot. Each group is 5 games and uses one unit of the team's shared quota
(50 groups, rolling one hour from the first use). The panel is 18 groups (90 games; 60 before 2026-10-28 14:25Z). By default `panel` keeps
`--reserve` 10 units for teammates.

    python3 tools/scrim.py timelines <version>   # re-download a version's replays to rebuild timelines

Files: data/scrims/groups.jsonl (one row per group), data/scrims/<version>/{summaries,analysis,features.jsonl}.
analysis/ keeps each replay's report, stats and timeline CSV, so `tools/fights.py data/scrims/<version>/analysis
--features data/scrims/<version>/features.jsonl` runs on any version.
"""
import argparse
import collections
import json
import statistics
import subprocess
import time
import zipfile
from pathlib import Path

import arena
import features
import ranked

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "data" / "scrims"
GROUPS = DIR / "groups.jsonl"

# Opponents: teams that beat us most in ranked (v17-v22, 2026-10-27/28; EternalWisdom builds 79% Power, B59) and
# two top-5 teams for the gap to the top. Maps: our worst ranked maps, then a set of common ones.
PANEL_TEAMS = [
    ("eeb96607-55bb-421b-9868-38767018cb93", "Aynir Industries"),
    ("6f67dab5-8edd-4700-b33b-71c2df1dc881", "noobers"),
    ("aa795cbd-97f0-489d-868b-2988d7b2e394", "The Onkeys"),
    ("05c4d857-1412-4c63-8c8e-ad05df77f193", "EternalWisdom"),
    ("1890540d-1ffc-4847-adbf-d0d08772f268", "Intercontinental Fish"),
    ("695ddbdf-afd9-43bf-9988-2a98fdb0f750", "Micron"),
]
PANEL_MAPS = [
    ("00ribs,01corridors,00galaxy,00vault,00eight", "a,b,a,b,a"),
    ("00stampede,00swirl,02geodes,00lanes,00expanse", "b,a,b,a,b"),
    # Added 2026-10-28 14:25Z: maps of v25's ranked losses, so the panel is not only our worst maps (90 games a version).
    ("01islands,01starfish,02arena,00collision,02the_pond", "a,b,a,b,a"),
]


def cambc(*args, retries=5):
    for attempt in range(retries):
        out = subprocess.run([arena.CAMBC, *args], capture_output=True, text=True)
        if out.returncode == 0 or "429" not in out.stderr + out.stdout:
            return out
        time.sleep(6 * (attempt + 1))
    return out


def groups():
    return [json.loads(l) for l in GROUPS.read_text().splitlines()] if GROUPS.exists() else []


def save(rows):
    GROUPS.write_text("".join(json.dumps(r) + "\n" for r in rows))


def live():
    """(version, submission time) of the last `ladder.py submitted` entry."""
    last = json.loads((ROOT / "docs" / "submissions.jsonl").read_text().splitlines()[-1])
    return Path(last["bot"]).name, last["time"]


def quota():
    out = cambc("match-groups", "quota", "--json")
    if out.returncode:
        raise SystemExit(out.stderr)
    return json.loads(out.stdout)["quota"]


def create(team_id, team, maps, sides, version, purpose):
    out = cambc("match-groups", "create", team_id, "--maps", maps, "--sides", sides, "--json")
    if out.returncode:
        print("create failed", team, out.stderr.strip()[-200:])
        return None
    row = {"group": json.loads(out.stdout)["groupId"], "team": team, "teamId": team_id, "maps": maps,
           "sides": sides, "version": version, "purpose": purpose,
           "created": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "done": False}
    save(groups() + [row])
    print("queued", team, maps, row["group"])
    return row


def panel(reserve):
    version, _ = live()
    have = {(g["teamId"], g["maps"]) for g in groups() if g["version"] == version}
    todo = [(t, n, m, s) for t, n in PANEL_TEAMS for m, s in PANEL_MAPS if (t, m) not in have]
    q = quota()
    room = q["limit"] - q["used"] - reserve
    print(f"{version}: {len(todo)} panel groups to queue, quota {q['used']}/{q['limit']} (resets {q['resetsAt']})")
    for t, n, m, s in todo[:max(0, room)]:
        create(t, n, m, s, version, "panel")


def analyze(zip_path, out):
    """Decode a replay into <out>/<match id>.txt, .stats.json and .timeline.csv (kept for tools/fights.py)."""
    report = subprocess.run(["node", str(ROOT / "tools/replay/analyze.mjs"), "--out", str(out), str(zip_path)],
                            capture_output=True, text=True)
    if report.returncode:
        print("analyze failed", zip_path.name, report.stderr.strip()[-300:])
        return
    (out / f"{zip_path.stem}.txt").write_text(report.stdout)
    zip_path.unlink()


def unpack(group, vdir):
    """Download a finished group's five replays and decode each into vdir/analysis."""
    bundle = vdir / f"{group}.zip"
    if cambc("match-groups", "download", group, "-o", str(bundle)).returncode:
        return
    with zipfile.ZipFile(bundle) as z:
        for name in z.namelist():
            target = vdir / "analysis" / (name.split("-", 1)[1] if "-" in name else name)
            target.write_bytes(z.read(name))
            analyze(target, vdir / "analysis")
    bundle.unlink()


def timelines(version):
    vdir = DIR / version
    (vdir / "analysis").mkdir(parents=True, exist_ok=True)
    for g in groups():
        if g["version"] == version and g["done"]:
            unpack(g["group"], vdir)
            print("decoded", g["team"], g["group"])


def sync():
    rows = groups()
    for g in rows:
        if g["done"]:
            continue
        out = cambc("match-groups", "show", g["group"], "--json")
        if out.returncode:
            continue
        matches = json.loads(out.stdout)["matches"]
        if any(m["status"] != "finished" for m in matches):
            continue
        vdir = DIR / g["version"]
        (vdir / "summaries").mkdir(parents=True, exist_ok=True)
        (vdir / "analysis").mkdir(exist_ok=True)
        unpack(g["group"], vdir)
        feats = vdir / "features.jsonl"
        seen = {json.loads(l)["match"] for l in feats.read_text().splitlines()} if feats.exists() else set()
        with feats.open("a") as f:
            for m in matches:
                if m["matchId"] in seen:
                    continue
                us = next(t for t in m["teams"] if t["name"] == "Deer Park")
                path = vdir / "summaries" / f"{m['matchId']}.json"
                if not ranked.download(m["matchId"], path, "summary", "--json"):
                    continue
                ranked.save_gzipped(path)
                s = features.load(Path(f"{path}.gz"))
                row = features.row(s, "team" + us["side"].upper(), m["matchId"], m["map"], us["result"] == "win")
                f.write(json.dumps(row | {"team": g["team"], "group": g["group"], "purpose": g["purpose"]}) + "\n")
        g["done"] = True
        save(rows)
        print("synced", g["version"], g["team"], g["group"])


def report():
    for vdir in sorted(p for p in DIR.iterdir() if (p / "features.jsonl").exists()):
        rows = [json.loads(l) for l in (vdir / "features.jsonl").read_text().splitlines()]
        wins = sum(r["win"] for r in rows)
        mean = lambda k: statistics.mean(r[k] for r in rows if isinstance(r.get(k), (int, float)))
        print(f"\n== {vdir.name}: {wins}-{len(rows) - wins} over {len(rows)} scrims; gold {mean('earnedGold'):.0f}, "
              f"clears {mean('camp_clears'):.1f}, deaths {mean('deaths'):.1f}, gems r500 {mean('gems_r500'):.0f}")
        for key in ("team", "map"):
            tally = collections.defaultdict(lambda: [0, 0])
            for r in rows:
                tally[r[key]][0] += r["win"]
                tally[r[key]][1] += 1
            print(f"  by {key}: " + ", ".join(f"{k} {w}-{n - w}" for k, (w, n) in sorted(tally.items())))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["panel", "create", "sync", "report", "quota", "timelines"])
    parser.add_argument("team", nargs="?")
    parser.add_argument("--maps")
    parser.add_argument("--sides", default="a,b,a,b,a")
    parser.add_argument("--reserve", type=int, default=10, help="quota units left for teammates")
    args = parser.parse_args()
    DIR.mkdir(parents=True, exist_ok=True)
    if args.command == "panel":
        panel(args.reserve)
    elif args.command == "create":
        create(args.team, args.team, args.maps, args.sides, live()[0], "adhoc")
    elif args.command == "sync":
        sync()
    elif args.command == "report":
        report()
    elif args.command == "timelines":
        timelines(args.team)
    else:
        print(quota())


if __name__ == "__main__":
    main()
