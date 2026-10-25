#!/usr/bin/env python3
"""Race several variants of one change against a base and keep the best (Phase 2 item 9; successive halving).

    python3 tools/race.py bots/daniel/v10 bots/_var/a bots/_var/b bots/_var/c [--rounds 3]

Round k plays every surviving variant against the base on every map, both sides, at fresh draft seeds (2^k seeds:
1, 2, 4, ...), adds the results to its running score, and drops the worse half. The last survivor is printed with
its record. It is the best of several noisy candidates, so it is biased upwards: confirm it with
`tools/gate.py <winner> <base>`, whose seeds start at 0 and are fresh to it. Build variants as copies of the
candidate folder (e.g. under bots/_var/, gitignored) that differ in one place each.
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("base")
    parser.add_argument("variants", nargs="+")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--first-seed", type=int, default=1000, help="seeds used here start at this number")
    parser.add_argument("--jobs", type=int, default=os.cpu_count())
    args = parser.parse_args()

    base = arena.bot_path(args.base)
    arena.build(base)
    alive = [arena.bot_path(v) for v in args.variants]
    for v in alive:
        arena.build(v)
    score = {v: [0, 0] for v in alive}
    seed = args.first_seed
    for k in range(args.rounds):
        seeds = list(range(seed, seed + 2 ** k))
        seed += len(seeds)
        for v in alive:
            for _, a_first, stats in arena.run_matches(v, base, arena.maps(), repeat=0, jobs=args.jobs, seeds=seeds):
                if stats:
                    score[v][0] += arena.a_result(a_first, stats)[0]
                    score[v][1] += 1
        ranked = sorted(alive, key=lambda v: score[v][0] / max(score[v][1], 1), reverse=True)
        print(f"round {k}: " + ", ".join(f"{v.name} {score[v][0]}/{score[v][1]}" for v in ranked), flush=True)
        alive = ranked[:max(1, len(ranked) // 2)]
        if len(alive) == 1 and k + 1 < args.rounds:
            break
    winner = alive[0]
    w, n = score[winner]
    print(f"winner: {winner} ({w}/{n} = {w / max(n, 1):.0%} vs {base.name}); confirm with tools/gate.py {winner} {base}")


if __name__ == "__main__":
    main()
