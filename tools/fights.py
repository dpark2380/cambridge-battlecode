#!/usr/bin/env python3
"""Fight and grouping statistics from decoded replay timelines (stdlib only).

    python3 tools/fights.py replays/daniel-e3 data/scout/replays --since 2026-11-04T23:00Z

Each folder holds <match>.timeline.csv[.gz] (tools/replay/analyze.mjs) and <match>.json naming the focal team's side
(ranked downloads: our side; data/scout/replays: the scouted team's side). Folders are reported separately, and
data/scout/replays is split by the scouted team's rank (top 3, 4-10, 11+).

Per focal champion and round (positions sampled at round start):
  contact   an enemy champion alive within CONTACT tiles (Chebyshev)
  episode   a run of contact rounds (gaps up to 2 rounds join), started with N allies (self included) and M enemies
            within GROUP tiles of the champion; it ends in "died" (the champion's deaths count rises during it or
            within 2 rounds after), "kill" (the team's kills rise and the champion survives) or "apart"
Prints per 1000 champion-rounds: deaths, kills, contact share; dead share; allies within GROUP tiles by phase; and
episodes by starting numbers (outnumbered / even / ahead) with how often each ends in a death or a kill.
"""
import argparse
import collections
import csv
import gzip
import json
import sys
from pathlib import Path

CONTACT = 4
GROUP = 6
PHASES = ((0, 500), (500, 1000), (1000, 2001))


def read_timeline(path):
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as f:
        rows = list(csv.DictReader(f))
    rounds = collections.defaultdict(list)
    for r in rows:
        rounds[int(r["round"])].append(r)
    return rounds


def game_stats(rounds, side, acc):
    side = side.upper()
    open_ep = {}  # champion -> episode dict
    last = {}
    team_kills_prev = 0
    for rnd in sorted(rounds):
        rows = rounds[rnd]
        ours = [r for r in rows if r["team"] == side]
        theirs = [r for r in rows if r["team"] != side and r["alive"] == "1"]
        team_kills = sum(int(r["kills"]) for r in ours)
        phase = next(i for i, (a, b) in enumerate(PHASES) if a <= rnd < b)
        for r in ours:
            c = r["champion"]
            acc["rounds"] += 1
            prev = last.get(c)
            died = prev is not None and int(r["deaths"]) > int(prev["deaths"])
            if died:
                acc["deaths"] += 1
            last[c] = r
            ep = open_ep.get(c)
            if ep and died:
                ep["end"] = "died"
            if r["alive"] != "1":
                acc["dead_rounds"] += 1
                if ep:
                    close(ep, acc)
                    del open_ep[c]
                continue
            x, y = int(r["x"]), int(r["y"])
            near = lambda o, d: max(abs(int(o["x"]) - x), abs(int(o["y"]) - y)) <= d
            allies = sum(1 for o in ours if o["alive"] == "1" and near(o, GROUP))
            acc["allies_by_phase"][phase] += allies
            acc["alive_by_phase"][phase] += 1
            contact = any(near(o, CONTACT) for o in theirs)
            if contact:
                acc["contact_rounds"] += 1
                if not ep:
                    enemies = sum(1 for o in theirs if near(o, GROUP))
                    hp = float(r["health"]) / max(1.0, float(r["maxHealth"]))
                    ep = open_ep[c] = {"allies": allies, "enemies": enemies, "hp": hp, "gems": int(r["gems"]),
                                       "last": rnd, "end": "apart", "kills0": team_kills}
                ep["last"] = rnd
            elif ep and rnd - ep["last"] > 2:
                if team_kills > ep["kills0"] and ep["end"] != "died":
                    ep["end"] = "kill"
                close(ep, acc)
                del open_ep[c]
            elif ep and team_kills > ep["kills0"] and ep["end"] != "died":
                ep["end"] = "kill"
        team_kills_prev = team_kills
    acc["kills"] += team_kills_prev
    for ep in open_ep.values():
        close(ep, acc)


def close(ep, acc):
    d = ep["allies"] - ep["enemies"]
    odds = "outnumbered" if d < 0 else "even" if d == 0 else "ahead"
    hp = "hurt" if ep["hp"] < 0.5 else "healthy"
    acc["episodes"][(odds, ep["end"])] += 1
    acc["episodes_hp"][(hp, ep["end"])] += 1
    if ep["gems"] >= 20:
        acc["episodes_carrier"][ep["end"]] += 1


def new_acc():
    return {"games": 0, "wins": 0, "rounds": 0, "deaths": 0, "kills": 0, "dead_rounds": 0, "contact_rounds": 0,
            "allies_by_phase": [0, 0, 0], "alive_by_phase": [0, 0, 0], "episodes": collections.Counter(),
            "episodes_hp": collections.Counter(), "episodes_carrier": collections.Counter()}


def report(name, a):
    if not a["games"]:
        return
    k = 1000 / a["rounds"]
    print(f"\n== {name}: {a['games']} games, win {100 * a['wins'] / a['games']:.0f}%")
    print(f"   per 1000 champion-rounds: deaths {a['deaths'] * k:.2f}  kills {a['kills'] * k:.2f}  "
          f"in contact {a['contact_rounds'] * k:.0f}  dead {a['dead_rounds'] * k:.0f}")
    print("   allies within %d tiles (self incl.) by phase: " % GROUP +
          "  ".join(f"r{p[0]}-{p[1]} {a['allies_by_phase'][i] / max(1, a['alive_by_phase'][i]):.2f}" for i, p in enumerate(PHASES)))
    eps = a["episodes"]
    total = sum(eps.values())
    print(f"   contact episodes {total / a['games']:.1f}/game; by starting numbers (share, died%, kill%):")
    for odds in ("outnumbered", "even", "ahead"):
        n = sum(v for (o, _), v in eps.items() if o == odds)
        if n:
            print(f"     {odds:11s} {100 * n / total:4.0f}%  died {100 * eps[(odds, 'died')] / n:4.1f}%  kill {100 * eps[(odds, 'kill')] / n:4.1f}%")
    for hp in ("healthy", "hurt"):
        n = sum(v for (h, _), v in a["episodes_hp"].items() if h == hp)
        if n:
            print(f"     {hp:11s} {100 * n / total:4.0f}%  died {100 * a['episodes_hp'][(hp, 'died')] / n:4.1f}%  kill {100 * a['episodes_hp'][(hp, 'kill')] / n:4.1f}%")
    n = sum(a["episodes_carrier"].values())
    if n:
        print(f"     carrier20+  {100 * n / total:4.0f}%  died {100 * a['episodes_carrier']['died'] / n:4.1f}%")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--since", default="", help="only games finished/created at or after this ISO time")
    a = ap.parse_args()
    for folder in a.folders:
        groups = collections.defaultdict(new_acc)
        for meta_path in sorted(Path(folder).glob("*.json")):
            if meta_path.name.endswith(".stats.json"):
                continue
            meta = json.loads(meta_path.read_text())
            when = meta.get("finished") or meta.get("created") or ""
            if when < a.since:
                continue
            tl = next((p for p in (meta_path.with_suffix(".timeline.csv.gz"), meta_path.with_suffix(".timeline.csv")) if p.exists()), None)
            if not tl:
                continue
            rank = meta.get("rank")
            key = folder if rank is None else f"{folder} rank {'1-3' if rank <= 3 else '4-10' if rank <= 10 else '11+'}"
            acc = groups[key]
            try:
                game_stats(read_timeline(tl), meta["side"], acc)
            except (KeyError, ValueError, StopIteration) as e:
                print(f"skip {meta_path.name}: {e}", file=sys.stderr)
                continue
            acc["games"] += 1
            acc["wins"] += bool(meta.get("win"))
        for key in sorted(groups):
            report(key, groups[key])


if __name__ == "__main__":
    main()
