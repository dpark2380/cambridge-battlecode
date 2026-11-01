#!/usr/bin/env python3
"""Per-map camp-group capture lists, ours vs the opponents, from a scrim panel version (stdlib only).

    python3 tools/captures.py v47            # data/scrims/v47: captures and gems per group per game, both sides

Panel sides are fixed per map, so a group id is on the same side in every game of a map. One capture = one
(side, group, round) in the gemCollection events; gems are what that side received. Rewards come from
maps/ascii/<map>.txt. Process review 2026-11-01 H1: equal capture counts, half the gems captured (B128).
"""
import collections
import json
import re
import sys
from pathlib import Path

import features

ROOT = Path(__file__).resolve().parent.parent


def rewards(map_name):
    out = {}
    for line in (ROOT / "maps" / "ascii" / f"{map_name.replace('_', '-')}.txt").read_text().splitlines():
        m = re.match(r"# G(\d+) (\{.*?\}) gems=(\d+) gold=(\d+)", line)
        if m:
            out[int(m[1])] = (m[2], int(m[3]), int(m[4]))
    return out


def main():
    version = sys.argv[1]
    vdir = ROOT / "data" / "scrims" / version
    rows = [json.loads(l) for l in (vdir / "features.jsonl").read_text().splitlines()]
    per_map = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0, 0]))  # gid -> our caps, our gems, their caps, their gems
    games = collections.Counter()
    for r in rows:
        path = vdir / "summaries" / f"{r['match']}.json.gz"
        if not path.exists():
            continue
        s = features.load(path)
        games[r["map"]] += 1
        seen = set()
        for e in s["events"]:
            if e["kind"] != "gemCollection":
                continue
            mine = e["owner"]["team"] == r["side"]
            for x in e["entries"]:
                if x["context"] != "campGroup":
                    continue
                gid = x["target"]["id"]
                c = per_map[r["map"]][gid]
                i = 0 if mine else 2
                if (mine, gid, x["timestamp"]["round"]) not in seen:
                    c[i] += 1
                    seen.add((mine, gid, x["timestamp"]["round"]))
                c[i + 1] += int(x["value"])
    total = [0, 0, 0, 0]
    for map_name, g in sorted(per_map.items()):
        rw, n = rewards(map_name), games[map_name]
        sums = [sum(v[k] for v in g.values()) / n for k in range(4)]
        total = [a + b for a, b in zip(total, sums)]
        print(f"\n== {map_name} ({n} games): captures/game us {sums[0]:.1f} them {sums[2]:.1f}; "
              f"gems captured us {sums[1]:.0f} them {sums[3]:.0f}")
        by_gap = sorted(g.items(), key=lambda kv: kv[1][3] - kv[1][1], reverse=True)
        for gid, (oc, og, tc, tg) in by_gap[:4] + [d for d in by_gap[-2:] if d not in by_gap[:4]]:
            comp, gems, gold = rw.get(gid, ("?", 0, 0))
            print(f"   G{gid:<3d} {comp:28s} gems={gems:<4d} gold={gold:<4d}  us {oc / n:4.1f} caps {og / n:5.0f} gems "
                  f"| them {tc / n:4.1f} caps {tg / n:5.0f} gems")
    k = len(per_map)
    print(f"\nALL maps avg: captures us {total[0] / k:.1f} them {total[2] / k:.1f}; "
          f"gems captured us {total[1] / k:.0f} them {total[3] / k:.0f}")


if __name__ == "__main__":
    main()
