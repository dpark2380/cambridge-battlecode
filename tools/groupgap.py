#!/usr/bin/env python3
"""Camp groups the opponents farm and we skip, from ranked (or scrim) summaries (stdlib only; B137-B143).

    python3 tools/groupgap.py replays/daniel-v51 replays/daniel-v52 ...    # ranked.py folders
    python3 tools/groupgap.py data/scrims/v59p2                            # a scrim panel

Each capture (a gemCollection event from a camp group) is matched to the nearest group centroid in
maps/ascii/<map>.txt. Prints groups worth 10+ gems that the opponents capture 2+ times a game and we
capture at most 40% as often, ranked by gems lost a game. Pathing traps (camps sealed by holes or by
their own group) show up here first.
"""
import collections
import glob
import gzip
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def map_groups():
    groups = {}
    for f in glob.glob(os.path.join(ROOT, 'maps', 'ascii', '*.txt')):
        gs = {}
        for line in open(f):
            m = re.match(r"# G(\d+) (\{.*\}) gems=(\d+) gold=(\d+) respawn=\d+ at=\((\d+),(\d+)\)", line)
            if m:
                gs[int(m[1])] = (int(m[5]), int(m[6]), m[2], int(m[3]), int(m[4]))
        groups[os.path.basename(f)[:-4].replace('-', '_')] = gs
    return groups


def main(dirs):
    groups = map_groups()
    ours, theirs = collections.defaultdict(collections.Counter), collections.defaultdict(collections.Counter)
    games = collections.Counter()
    for d in dirs:
        rows = {}
        for line in open(os.path.join(d, 'features.jsonl')):
            r = json.loads(line)
            rows[r['match']] = r
        for p in glob.glob(os.path.join(d, 'summaries', '*')):
            r = rows.get(os.path.basename(p).split('.')[0])
            gs = r and groups.get(r['map'])
            if not gs:
                continue
            try:
                s = json.load(gzip.open(p) if p.endswith('.gz') else open(p))
            except (OSError, ValueError):
                continue
            us = r.get('side') or r.get('team')
            games[r['map']] += 1
            seen = set()
            for e in s.get('events', []):
                if e['kind'] != 'gemCollection':
                    continue
                for x in e['entries']:
                    if x.get('context') != 'campGroup':
                        continue
                    g = min(gs, key=lambda k: (gs[k][0] - x['x']) ** 2 + (gs[k][1] - x['y']) ** 2)
                    key = (e['owner']['team'], g, x['timestamp']['round'])  # one capture, split among receivers
                    if key not in seen:
                        seen.add(key)
                        (ours if e['owner']['team'] == us else theirs)[r['map']][g] += 1
    out = []
    for mp, n in games.items():
        for g, (_, _, comp, gems, gold) in groups[mp].items():
            o, t = ours[mp][g] / n, theirs[mp][g] / n
            if t >= 2 and o <= 0.4 * t and gems >= 10:
                out.append(((t - o) * gems, mp, g, comp, gems, gold, o, t, n))
    for lost, mp, g, comp, gems, gold, o, t, n in sorted(out, reverse=True)[:30]:
        print(f"{mp:22s} G{g:<3d} {comp[:34]:34s} gems {gems:4d} gold {gold:4d}  ours {o:5.1f}  theirs {t:5.1f}  (n={n})  lost/game {lost:.0f}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(sys.argv[1:])
