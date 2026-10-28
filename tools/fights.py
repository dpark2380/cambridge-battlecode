#!/usr/bin/env python3
"""Fight metrics from decoded replay timelines (stdlib only; docs/research/path-to-60-2026-10-28.md).

    node tools/replay/analyze.mjs --out DIR replay.zip ...      # writes DIR/<match id>.timeline.csv
    python3 tools/fights.py DIR... --features data/scrims/v22/features.jsonl replays/daniel-v22/features.jsonl

Our side per match comes from the features rows (`side`). Timeline rows are sampled at the start of each round.
For both teams it prints:
  engagement   an enemy within 4 tiles after 10 rounds without one; died = dead within 24 rounds. Split by the
               count of enemies within 4 and allies within 5 at contact, and (1 enemy, 0 allies, health >= 80%)
               by champion type.
  low health   health < 50% with an enemy within 4; died = dead within 20 rounds (then skip 25 rounds).
  retreating   share of deaths where the victim ended the last 8 rounds more than one tile closer to its spawn.
  adjacent     share of rounds with an enemy within 4 in which the nearest enemy is adjacent, per champion type.
"""
import argparse
import collections
import csv
import glob
import json
import sys
from pathlib import Path


def dist(a, b):
    return max(abs(int(a["x"]) - int(b["x"])), abs(int(a["y"]) - int(b["y"])))


def load(path):
    rounds = collections.defaultdict(dict)
    with open(path) as f:
        for row in csv.DictReader(f):
            rounds[int(row["round"])][row["champion"]] = row
    return rounds


def died_within(T, c, r, n):
    d0 = int(T[r][c]["deaths"])
    return any(int(T.get(r + b, {}).get(c, T[r][c])["deaths"]) > d0 for b in range(1, n + 1))


def analyse(T, us, acc):
    first = min(T)
    spawn = {c: o for c, o in T[first].items()}
    for c, o0 in T[first].items():
        team = o0["team"]
        who = "us" if team == us else "them"
        quiet, skip_until = 99, -1
        for r in sorted(T):
            o = T[r].get(c)
            if not o or o["alive"] != "1":
                quiet = 99
                continue
            enemies = [e for e in T[r].values() if e["team"] != team and e["alive"] == "1" and dist(o, e) <= 4]
            allies = [a for k, a in T[r].items() if k != c and a["team"] == team and a["alive"] == "1" and dist(o, a) <= 5]
            hp = float(o["health"]) / float(o["maxHealth"])
            if enemies:
                acc[who]["adj"][o["type"]][1] += 1
                acc[who]["adj"][o["type"]][0] += min(dist(o, e) for e in enemies) <= 1
            if enemies and quiet >= 10:
                died = died_within(T, c, r, 24)
                key = (min(len(enemies), 3), min(len(allies), 2))
                acc[who]["eng"]["all"][0] += died
                acc[who]["eng"]["all"][1] += 1
                acc[who]["eng"][key][0] += died
                acc[who]["eng"][key][1] += 1
                if key == (1, 0) and hp >= 0.8:
                    acc[who]["duel"][o["type"]][0] += died
                    acc[who]["duel"][o["type"]][1] += 1
            if enemies and hp < 0.5 and r >= skip_until:
                acc[who]["low"]["all"][0] += died_within(T, c, r, 20)
                acc[who]["low"]["all"][1] += 1
                skip_until = r + 25
            quiet = 0 if enemies else quiet + 1
    # deaths while walking home
    prev = {}
    for r in sorted(T):
        for c, o in T[r].items():
            d = int(o["deaths"])
            if c in prev and d > prev[c]:
                seq = [T.get(r - b, {}).get(c) for b in range(8, 1, -1)]
                seq = [s for s in seq if s and s["alive"] == "1"]
                if len(seq) >= 4:
                    home = spawn[c]
                    toward = dist(seq[-1], home) < dist(seq[0], home) - 1
                    who = "us" if o["team"] == us else "them"
                    acc[who]["retreat"][o["type"]][0] += toward
                    acc[who]["retreat"][o["type"]][1] += 1
            prev[c] = d


def pct(pair):
    return f"{100 * pair[0] / pair[1]:.0f}% of {pair[1]}" if pair[1] else "-"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("dirs", nargs="+")
    p.add_argument("--features", nargs="+", required=True)
    args = p.parse_args()
    side = {}
    for f in args.features:
        for line in open(f):
            r = json.loads(line)
            side[r["match"]] = "A" if r["side"] == "teamA" else "B"
    new = lambda: collections.defaultdict(lambda: [0, 0])
    acc = {w: collections.defaultdict(new) for w in ("us", "them")}
    games = 0
    for d in args.dirs:
        for path in sorted(glob.glob(str(Path(d) / "*.timeline.csv"))):
            mid = Path(path).name.split(".")[0]
            if mid not in side:
                print("no features row for", mid, file=sys.stderr)
                continue
            analyse(load(path), side[mid], acc)
            games += 1
    print(f"{games} games")
    for who in ("us", "them"):
        a = acc[who]
        print(f"== {who}")
        print(f"  engagements: died {pct(a['eng']['all'])}; low health near an enemy: died {pct(a['low']['all'])}")
        print("  by (enemies, allies):", {k: pct(v) for k, v in sorted((k, v) for k, v in a["eng"].items() if k != "all") if v[1] >= 10})
        print("  healthy 1v1 by type:", {k: pct(v) for k, v in sorted(a["duel"].items()) if v[1] >= 5})
        tot = [sum(v[0] for v in a["retreat"].values()), sum(v[1] for v in a["retreat"].values())]
        print(f"  deaths while walking home: {pct(tot)};", {k: pct(v) for k, v in sorted(a["retreat"].items()) if v[1] >= 5})
        print("  adjacent while in contact:", {k: pct(v) for k, v in sorted(a["adj"].items()) if v[1] >= 200})


if __name__ == "__main__":
    main()
