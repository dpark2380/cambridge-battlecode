#!/usr/bin/env python3
"""Compare openings: which camp groups each side clears first, and when (backlog B16; stdlib only).

    python3 tools/openings.py 00elkring 01hooks --ours replays/daniel-v9 replays/daniel-v10

For each map, prints the first --clears camp clears (round, group id, its gems/gold from maps/ascii) of every
top-team side in data/scout/summaries and of our side in the --ours folders, then the median round of the 1st,
3rd and 5th clear. Group ids are the engine's camp group ids, the same as `G<n>` in maps/ascii/<map>.txt.
"""
import argparse
import collections
import glob
import json
import re
import statistics
from pathlib import Path

import features

ROOT = Path(__file__).resolve().parent.parent


def groups(map_name):
    """{group id: (gems, gold)} from the map dump (listing names use '_', files '-')."""
    path = ROOT / "maps" / "ascii" / f"{map_name.replace('_', '-')}.txt"
    out = {}
    if path.exists():
        for m in re.finditer(r"# G(\d+) .*?gems=(\d+) gold=(\d+)", path.read_text()):
            out[int(m.group(1))] = (int(m.group(2)), int(m.group(3)))
    return out


def clears(summary, side):
    rows = []
    for e in summary.get("events", []):
        if e["kind"] == "campClear" and e["owner"].get("team") == side:
            for entry in e["entries"]:
                rows.append((entry["timestamp"]["round"], entry["target"]["id"]))
    return sorted(set(rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("maps", nargs="+", help="listing names, e.g. 00elkring")
    parser.add_argument("--ours", nargs="*", default=[])
    parser.add_argument("--team", default="Deer Park")
    parser.add_argument("--clears", type=int, default=6)
    args = parser.parse_args()

    tally = json.loads(Path(sorted(glob.glob(str(ROOT / "data/scout/2*.json")))[-1]).read_text())
    top = {g["match"]: (g["side"], e["name"], g["win"], g["map"]) for e in tally for g in e["games"]}
    ours = {}
    for folder in args.ours:
        for m in json.loads((Path(folder) / "matches.json").read_text()):
            us = next(t for t in m["teams"] if t["name"] == args.team)
            ours[m["matchId"]] = (us["side"], "US", us["result"] == "win", m["map"], Path(folder))

    for map_name in args.maps:
        g = groups(map_name)
        print(f"\n## {map_name}")
        stats = collections.defaultdict(lambda: collections.defaultdict(list))
        for mid, (side, who, won, m) in top.items():
            path = ROOT / "data" / "scout" / "summaries" / f"{mid}.json.gz"
            if m == map_name and path.exists():
                seq = clears(features.load(path), "team" + side.upper())
                show(who, won, seq, g, args.clears, stats["top"])
        for mid, (side, who, won, m, folder) in ours.items():
            path = folder / "summaries" / f"{mid}.json.gz"
            if m == map_name and path.exists():
                seq = clears(features.load(path), "team" + side.upper())
                show("US", won, seq, g, args.clears, stats["us"])
        for who, s in stats.items():
            print(f"  median round of clear #1/#3/#5 ({who}): "
                  + " / ".join(f"{statistics.median(s[k]):.0f}" if s[k] else "-" for k in (1, 3, 5)))


def show(who, won, seq, g, n, stats):
    for k in (1, 3, 5):
        if len(seq) >= k:
            stats[k].append(seq[k - 1][0])
    cells = [f"r{r} G{gid}({g.get(gid, ('?', '?'))[0]}g/{g.get(gid, ('?', '?'))[1]}$)" for r, gid in seq[:n]]
    print(f"  {who[:20]:20s} {'W' if won else 'L'}  " + "  ".join(cells))


if __name__ == "__main__":
    main()
