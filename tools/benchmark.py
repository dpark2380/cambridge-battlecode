#!/usr/bin/env python3
"""Where we fall furthest behind the top teams, per map (B13/T6; stdlib only).

    python3 tools/scout.py --top 20 --matches 100 --summaries 20      # fills data/scout/features.jsonl
    python3 tools/benchmark.py replays/daniel-v9/features.jsonl        # our rows vs the top 20's

Compares our feature rows (tools/ranked.py) with the top teams' (tools/scout.py) on each map: gems banked by
rounds 250/500/1000, gold earned, deaths, camp clears and the first clear. Gaps are in units of the top teams'
standard deviation on that map (z); the most negative gaps come first. Maps with fewer than 3 top-team games
are skipped. Use it to pick which part of the game to study in their replays (data/scout/replays).
"""
import argparse
import collections
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
# (metric, higher is better)
METRICS = [("gems_r250", True), ("gems_r500", True), ("gems_r1000", True), ("earnedGold", True),
           ("camp_clears", True), ("first_clear", False), ("deaths", False)]


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("ours")
    parser.add_argument("--top", default=str(ROOT / "data" / "scout" / "features.jsonl"))
    parser.add_argument("--min-games", type=int, default=3)
    args = parser.parse_args()
    ours, top = collections.defaultdict(list), collections.defaultdict(list)
    for r in rows(args.ours):
        ours[r["map"]].append(r)
    for r in rows(args.top):
        top[r["map"]].append(r)

    gaps = []
    for m in sorted(set(ours) & set(top)):
        if len(top[m]) < args.min_games:
            continue
        for metric, higher in METRICS:
            a = [r[metric] for r in ours[m] if r.get(metric) is not None]
            b = [r[metric] for r in top[m] if r.get(metric) is not None]
            if len(a) < 1 or len(b) < args.min_games:
                continue
            spread = statistics.pstdev(b) or 1.0
            z = (statistics.mean(a) - statistics.mean(b)) / spread * (1 if higher else -1)
            gaps.append((z, m, metric, statistics.mean(a), statistics.mean(b), len(a), len(b)))
    print(f"{'map':22s} {'metric':12s} {'ours':>8s} {'top':>8s} {'z':>6s}  games (ours/top)")
    for z, m, metric, a, b, na, nb in sorted(gaps)[:30]:
        print(f"{m:22s} {metric:12s} {a:8.0f} {b:8.0f} {z:+6.1f}  {na}/{nb}")
    by_metric = collections.defaultdict(list)
    for z, _, metric, *_ in gaps:
        by_metric[metric].append(z)
    print("\naverage gap per metric over maps (z; negative = we are behind):")
    for metric, zs in sorted(by_metric.items(), key=lambda kv: statistics.mean(kv[1])):
        print(f"  {metric:12s} {statistics.mean(zs):+.2f} over {len(zs)} maps")


if __name__ == "__main__":
    main()
