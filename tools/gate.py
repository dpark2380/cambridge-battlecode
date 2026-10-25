#!/usr/bin/env python3
"""Sequential gate for a candidate bot: paired, side-swapped games and an SPRT, Fishtest-style (T2).

    python3 tools/gate.py bots/daniel/v11 bots/daniel/v10                          # gain: is A better?
    python3 tools/gate.py bots/daniel/v11 bots/daniel/v10 --mode nonreg            # is A no worse?
    python3 tools/gate.py bots/daniel/v11 bots/daniel/v10 --mode map --maps 00packs   # a targeted fix

Games come in pairs: one map and one draft seed, played from both sides. A pair scores 0, 0.5 or 1 for A, which
removes the side advantage from the variance. Batches of pairs (every map once, at a fresh seed; seed 0 is the
real draft) are played until the log-likelihood ratio leaves [-2.94, 2.94] (alpha = beta = 0.05) or --max-seeds
runs out. LLR uses the normal approximation over pair scores: n (s1 - s0) (2 mean - s0 - s1) / (2 var), checked
after each batch and only from 30 pairs on (tools/test_gate.py simulates it: 4% false passes, 3% false fails).

Modes (H0 vs H1 as A's expected pair score):
  gain    0.50 vs 0.55   accept: A is better than B
  nonreg  0.45 vs 0.50   accept: A is no worse than B (H0 = A is clearly worse)
  map     0.50 vs 0.65   for a change aimed at --maps only; pair it with an all-map nonreg run

Exit status: 0 accepted H1 (pass), 1 accepted H0 (fail), 2 inconclusive at --max-seeds, 3 bot faults (smoke stage:
any crash of A fails at once). Prints the running LLR, the per-map record, and the decision.
"""
import argparse
import collections
import math
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena  # noqa: E402

MODES = {"gain": (0.50, 0.55), "nonreg": (0.45, 0.50), "map": (0.50, 0.65)}
BOUND = math.log((1 - 0.05) / 0.05)  # 2.944
MIN_PAIRS = 30  # the variance estimate is unreliable below this (simulated: 10-21% errors when stopping per pair)
# and never stop on the real-draft batch alone: it is one fixed draft per map


def llr(scores, s0, s1):
    """Normal-approximation log-likelihood ratio of H1 (mean s1) vs H0 (mean s0) for pair scores."""
    n = len(scores)
    if n < 2:
        return 0.0
    mean = sum(scores) / n
    var = sum((x - mean) ** 2 for x in scores) / (n - 1)
    var = max(var, 1e-3)  # all pairs equal: avoid dividing by zero
    return n * (s1 - s0) * (2 * mean - s0 - s1) / (2 * var)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bot_a")
    parser.add_argument("bot_b")
    parser.add_argument("--mode", choices=MODES, default="gain")
    parser.add_argument("--maps", nargs="*", default=None)
    parser.add_argument("--max-seeds", type=int, default=None,
                        help="batches beyond the real draft before giving up (default 12, and on few maps enough "
                             "batches for 4x the minimum pairs)")
    parser.add_argument("--jobs", type=int, default=os.cpu_count())
    args = parser.parse_args()

    s0, s1 = MODES[args.mode]
    bot_a, bot_b = arena.bot_path(args.bot_a), arena.bot_path(args.bot_b)
    arena.build(bot_a)
    arena.build(bot_b)
    maps = args.maps or arena.maps()
    if args.max_seeds is None:  # 12 seeds on 2 maps is 26 pairs: under MIN_PAIRS, so it could never decide
        args.max_seeds = max(12, 4 * MIN_PAIRS // len(maps))
    scores, per_map = [], collections.defaultdict(lambda: [0, 0])
    games = faults = 0
    print(f"{args.mode}: H0 {s0:.2f} vs H1 {s1:.2f} on {len(maps)} maps, pairs of side-swapped games", flush=True)
    for seed in range(args.max_seeds + 1):
        batch = collections.defaultdict(list)
        for m, a_first, stats in arena.run_matches(bot_a, bot_b, maps, repeat=1 if seed == 0 else 0, jobs=args.jobs,
                                                   seeds=() if seed == 0 else (seed,)):
            if stats is None:
                continue
            won, _, crash = arena.a_result(a_first, stats)
            faults += crash
            batch[m].append(won)
            per_map[m][0] += won
            per_map[m][1] += 1
            games += 1
        if faults:
            print(f"smoke: {Path(bot_a).name} crashed {faults} times; failing")
            sys.exit(3)
        scores += [sum(r) / 2 for r in batch.values() if len(r) == 2]
        value = llr(scores, s0, s1)
        mean = sum(scores) / max(len(scores), 1)
        print(f"seed {seed:2d}: {len(scores)} pairs, A's pair score {mean:.3f}, LLR {value:+.2f} "
              f"(bounds ±{BOUND:.2f})", flush=True)
        if abs(value) >= BOUND and len(scores) >= max(MIN_PAIRS, 2 * len(maps)):
            break

    for m, (w, n) in sorted(per_map.items()):
        print(f"  {m:24s} {w}/{n}")
    wins = sum(w for w, _ in per_map.values())
    print(f"{Path(bot_a).name} vs {Path(bot_b).name}: {wins}/{games} games = {wins / max(games, 1):.0%}")
    value = llr(scores, s0, s1) if len(scores) >= max(MIN_PAIRS, 2 * len(maps)) else 0.0
    if value >= BOUND:
        print(f"PASS ({args.mode}): accepted H1, A's pair score is about {s1:.2f} or better")
        sys.exit(0)
    if value <= -BOUND:
        print(f"FAIL ({args.mode}): accepted H0, A's pair score is about {s0:.2f} or worse")
        sys.exit(1)
    print(f"INCONCLUSIVE after {args.max_seeds} seeds (LLR {value:+.2f})")
    sys.exit(2)


if __name__ == "__main__":
    main()
