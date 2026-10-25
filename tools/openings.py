#!/usr/bin/env python3
"""Compare openings: which camp groups each side clears first, and when (backlog B16; stdlib only).

    python3 tools/openings.py 00elkring 01hooks --ours replays/daniel-v9 replays/daniel-v10
    python3 tools/openings.py --export bots/daniel/v12/src/openings.inc   # opening script table for the bot (B24)

For each map, prints the first --clears camp clears (round, group id, its gems/gold from maps/ascii) of every
top-team side in data/scout/summaries and of our side in the --ours folders, then the median round of the 1st,
3rd and 5th clear. Group ids are the engine's camp group ids, the same as `G<n>` in maps/ascii/<map>.txt.

--export writes, for every map with >= 4 scouted top-team games on a side, the 3 groups that appear most often in
that side's first 3 clears, as a C++ table keyed by map size, group count and total gems (unique over the pool),
with one team-A spawn tile to tell the sides apart.
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
    parser.add_argument("maps", nargs="*", help="listing names, e.g. 00elkring")
    parser.add_argument("--export")
    parser.add_argument("--ours", nargs="*", default=[])
    parser.add_argument("--team", default="Deer Park")
    parser.add_argument("--clears", type=int, default=6)
    args = parser.parse_args()

    top = {}
    for path in sorted(glob.glob(str(ROOT / "data/scout/2*.json"))):
        for e in json.loads(Path(path).read_text()):
            top.update({g["match"]: (g["side"], e["name"], g["win"], g["map"]) for g in e["games"]})
    if args.export:
        export(top, Path(args.export))
        return
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


def export(top, out, first=3, min_games=4):
    firsts = collections.defaultdict(list)
    for mid, (side, _, _, m) in top.items():
        path = ROOT / "data" / "scout" / "summaries" / f"{mid}.json.gz"
        if path.exists():
            seq = clears(features.load(path), "team" + side.upper())
            if seq:
                firsts[(m.replace("_", "-"), side.upper())].append({gid for _, gid in seq[:first]})
    rows = []
    for path in sorted((ROOT / "maps" / "ascii").glob("*.txt")):
        name, text = path.stem, path.read_text()
        grid = [m.group(1) for m in re.finditer(r"^\s*\d+  (\S+)$", text, re.M)]
        g = groups(name)
        a_spawn = next((x, y) for y, row in enumerate(grid) for x, ch in enumerate(row) if ch == "S")
        script = {}
        for side in "AB":
            games = firsts.get((name, side), [])
            if len(games) >= min_games:
                count = collections.Counter(gid for s in games for gid in s)
                script[side] = [gid for gid, _ in count.most_common(first)]
        if script:
            pad = lambda ids: ", ".join(str(i) for i in (ids + [-1] * first)[:first])
            rows.append(f"    {{{len(grid[0])}, {len(grid)}, {len(g)}, {sum(v[0] for v in g.values())}, "
                        f"{a_spawn[0]}, {a_spawn[1]}, {{{pad(script.get('A', []))}}}, {{{pad(script.get('B', []))}}}}},"
                        f"  // {name}")
    out.write_text("// Generated by tools/openings.py --export: the top 20's most common first 3 camp groups per map and side.\n"
                   "// {width, height, groups, total gems, team-A spawn x, y, {side A groups}, {side B groups}}\n"
                   + "\n".join(rows) + "\n")
    print(f"wrote {len(rows)} maps to {out}")


def show(who, won, seq, g, n, stats):
    for k in (1, 3, 5):
        if len(seq) >= k:
            stats[k].append(seq[k - 1][0])
    cells = [f"r{r} G{gid}({g.get(gid, ('?', '?'))[0]}g/{g.get(gid, ('?', '?'))[1]}$)" for r, gid in seq[:n]]
    print(f"  {who[:20]:20s} {'W' if won else 'L'}  " + "  ".join(cells))


if __name__ == "__main__":
    main()
