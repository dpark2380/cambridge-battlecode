#!/usr/bin/env python3
"""Round-robin over a pool of bots, Bradley-Terry ratings, and a mapping to the ladder (Phase 2 item 10).

    python3 tools/gauntlet.py                              # default pool, results cached in data/gauntlet/
    python3 tools/gauntlet.py --add bots/daniel/v11        # rate a candidate against the pool

Every pair plays every map from both sides, plus --seeds random drafts. Results are cached per pair
(data/gauntlet/<a>__<b>.json), so adding a bot only plays its own pairs. Ratings come from a batch
Bradley-Terry fit on an Elo scale (400 log10 odds), anchored so that Daniel v8 = 0, with a side term and
90% intervals from a bootstrap over (map, seed) groups. A batch fit, not incremental Elo: incremental systems depend on
game order (Halite rating study). Submitted versions with a ladder rating (docs/submissions.jsonl windows and
docs/ladder_history.csv) give a straight-line mapping from local rating to the ladder, printed when there are
two or more.
"""
import argparse
import csv
import json
import math
import os
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena  # noqa: E402

ROOT = arena.ROOT
POOL = ["bots/daniel/v7", "bots/daniel/v8", "bots/daniel/v9", "bots/daniel/v10", "bots/jame/v3", "bots/simon/v6",
        "bots/simon/hunter-v0"]
CACHE = ROOT / "data" / "gauntlet"


def key(bot):
    return str(Path(bot)).replace("/", "_")


def play_pair(a, b, seeds, jobs):
    path = CACHE / f"{key(a)}__{key(b)}.json"
    if path.exists():
        return json.loads(path.read_text())
    games, seen = [], {}
    for m, a_first, stats in arena.run_matches(arena.bot_path(a), arena.bot_path(b), arena.maps(), jobs=jobs,
                                               seeds=range(1, seeds + 1)):
        # Within a map and side, run_matches yields the real draft first, then the seeds in order: the n-th game
        # of (map, side) and of (map, other side) form one side-swapped pair, the bootstrap's resampling unit.
        n = seen.get((m, a_first), 0)
        seen[(m, a_first)] = n + 1
        if stats:
            games.append({"map": m, "a_first": a_first, "a_won": arena.a_result(a_first, stats)[0], "group": f"{m}#{n}"})
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(games))
    return games


def fit(results, bots, iters=200):
    """Bradley-Terry with a first-side term by gradient ascent; returns ({bot: rating}, side bonus) in Elo."""
    r = dict.fromkeys(bots, 0.0)
    side = 0.0
    lr = 20.0
    for _ in range(iters):
        grad = dict.fromkeys(bots, 0.0)
        gside = 0.0
        for a, b, a_first, a_won in results:
            diff = r[a] - r[b] + (side if a_first else -side)
            p = 1 / (1 + 10 ** (-diff / 400))
            e = (1.0 if a_won else 0.0) - p
            grad[a] += e
            grad[b] -= e
            gside += e if a_first else -e
        for bot in bots:
            r[bot] += lr * grad[bot] / max(1, len(results)) * len(bots)
        side += lr * gside / max(1, len(results))
    anchor = r.get("bots/daniel/v8", 0.0)
    return {bot: v - anchor for bot, v in r.items()}, side


def ladder_points():
    """{bot: ladder rating at the end of its submission window}."""
    subs = [json.loads(line) for line in (ROOT / "docs/submissions.jsonl").read_text().splitlines() if line.strip()]
    history = list(csv.DictReader((ROOT / "docs/ladder_history.csv").open()))
    points = {}
    for i, s in enumerate(subs):
        end = subs[i + 1]["time"] if i + 1 < len(subs) else "9999"
        window = [h for h in history if s["time"] <= h["time"] < end]
        if window:
            points[s["bot"]] = float(window[-1]["rating"])
    return points


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--add", nargs="*", default=[], help="bots to add to the default pool")
    parser.add_argument("--seeds", type=int, default=1)
    parser.add_argument("--boot", type=int, default=200)
    parser.add_argument("--jobs", type=int, default=os.cpu_count())
    args = parser.parse_args()
    bots = POOL + [b for b in args.add if b not in POOL]
    for b in bots:
        arena.build(arena.bot_path(b))

    results, groups = [], []
    for i, a in enumerate(bots):
        for b in bots[i + 1:]:
            games = play_pair(a, b, args.seeds, args.jobs)
            w = sum(g["a_won"] for g in games)
            print(f"  {a:22s} vs {b:22s} {w}/{len(games)}", flush=True)
            for g in games:
                results.append((a, b, g["a_first"], g["a_won"]))
                groups.append(f"{a}|{b}|{g['group']}")

    ratings, side = fit(results, bots)
    rng = random.Random(0)
    by_group = {}
    for res, grp in zip(results, groups):
        by_group.setdefault(grp, []).append(res)
    keys = list(by_group)
    boots = []
    for _ in range(args.boot):
        sample = [res for k in rng.choices(keys, k=len(keys)) for res in by_group[k]]
        boots.append(fit(sample, bots, iters=80)[0])
    print(f"\nBradley-Terry ratings (Elo scale, v8 = 0; first side {side:+.0f}):")
    points = ladder_points()
    for bot in sorted(bots, key=lambda b: -ratings[b]):
        vals = sorted(bs[bot] for bs in boots)
        lo, hi = vals[int(0.05 * len(vals))], vals[int(0.95 * len(vals)) - 1]
        ladder = f"  ladder {points[bot]:.0f}" if bot in points else ""
        print(f"  {bot:24s} {ratings[bot]:+6.0f}  [{lo:+.0f}, {hi:+.0f}]{ladder}")
    known = [(ratings[b], points[b]) for b in points if b in ratings]
    if len(known) >= 2:
        n = len(known)
        mx, my = sum(x for x, _ in known) / n, sum(y for _, y in known) / n
        sxx = sum((x - mx) ** 2 for x, _ in known) or 1.0
        slope = sum((x - mx) * (y - my) for x, y in known) / sxx
        print(f"\nladder ≈ {my - slope * mx:.0f} + {slope:.2f} × local, from {n} submitted versions "
              f"(rough until more versions have ladder windows):")
        for bot in sorted(bots, key=lambda b: -ratings[b]):
            print(f"  {bot:24s} predicted ladder {my + slope * (ratings[bot] - mx):.0f}")


if __name__ == "__main__":
    main()
