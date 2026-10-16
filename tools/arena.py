#!/usr/bin/env python3
"""Play bot A against bot B on every map from both sides, in parallel, and report A's results.

    python3 tools/arena.py main-cpp starter-cpp            # 9 maps x 2 sides
    python3 tools/arena.py main-cpp main-v1 --seeds 4      # + 4 random-draft games per map and side

Matches are deterministic, so --repeat only helps when a bot is nondeterministic. --seeds N adds games with
fuel quantum 1000000 + 10000*seed (seed_fuel), which main-cpp's draft turns into a random roster (paired by side swap);
use it to compare gameplay versions on many distinct games.

Bots are directories (bots/<name> or any path to a cambc bot project). Prints per-map results and
A's overall win rate with a 95% interval. Exit status is 0, so use --min-winrate to gate scripts.
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CAMBC = shutil.which("cambc") or str(Path.home() / ".local/bin/cambc")


def bot_path(name):
    """A path, a bot under bots/, or one under a teammate folder such as bots/daniel/."""
    path = Path(name)
    if path.exists():
        return path.resolve()
    for candidate in [ROOT / "bots" / name, *sorted((ROOT / "bots").glob(f"*/{name}"))]:
        if (candidate / "src").is_dir():
            return candidate
    return ROOT / "bots" / name


def build(bot):
    out = subprocess.run([CAMBC, "build", str(bot)], cwd=ROOT, capture_output=True, text=True)
    if out.returncode:
        sys.exit(f"build failed for {bot}:\n{out.stdout}{out.stderr}")


def play(bot_a, bot_b, map_name, fuel=None, keep_replay=None):
    """Run one match; return the statistics dict (None if the match failed)."""
    with tempfile.TemporaryDirectory() as tmp:
        stats = Path(tmp) / "stats.json"
        cmd = [CAMBC, "run", str(bot_a), str(bot_b), "--map", map_name, "-o", keep_replay or tmp,
               "--statistics", str(stats)]
        if fuel:
            cmd += ["--fuel", str(fuel)]
        subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
        return json.loads(stats.read_text()) if stats.exists() else None


def seed_fuel(seed):
    """Fuel quantum that main-cpp's draft decodes as experiment `seed` (random roster); see draft.cpp."""
    return 1_000_000 + 10_000 * seed


def maps():
    return sorted(p.stem for p in (ROOT / "maps").glob("*.map26a"))


def run_matches(bot_a, bot_b, map_names, repeat=1, jobs=os.cpu_count(), seeds=()):
    """Yield (map, a_is_team_a, stats) for every map, both sides, `repeat` times, plus each draft seed."""
    fuels = [None] * repeat + [seed_fuel(s) for s in seeds]
    games = [(m, side, f) for m in map_names for side in (True, False) for f in fuels]

    def one(game):
        m, a_first, fuel = game
        first, second = (bot_a, bot_b) if a_first else (bot_b, bot_a)
        return m, a_first, play(first, second, m, fuel)

    with ThreadPoolExecutor(jobs) as pool:
        yield from pool.map(one, games)


def a_result(a_first, stats):
    """(won, gem margin, a's crashes) from bot A's point of view."""
    a, b = (0, 1) if a_first else (1, 0)
    won = stats["outcome"] == ("teamA" if a_first else "teamB")
    gems = [t["submittedGems"] for t in stats["teams"]]
    return won, gems[a] - gems[b], stats["botFaults"][a]


def wilson(wins, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = wins / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - spread, centre + spread


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bot_a")
    parser.add_argument("bot_b")
    parser.add_argument("--maps", nargs="*", default=None)
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--seeds", type=int, default=0, help="extra random-draft games per map and side")
    parser.add_argument("--jobs", type=int, default=os.cpu_count())
    parser.add_argument("--min-winrate", type=float, default=None, help="exit 1 if A's win rate is below this")
    args = parser.parse_args()

    bot_a, bot_b = bot_path(args.bot_a), bot_path(args.bot_b)
    build(bot_a)
    build(bot_b)

    per_map = {}
    wins = games = faults = failed = 0
    for m, a_first, stats in run_matches(bot_a, bot_b, args.maps or maps(), args.repeat, args.jobs,
                                         range(1, args.seeds + 1)):
        if stats is None:
            failed += 1
            continue
        won, margin, crash = a_result(a_first, stats)
        per_map.setdefault(m, []).append((won, margin, stats["round"]))
        wins += won
        games += 1
        faults += crash

    for m, results in sorted(per_map.items()):
        w = sum(r[0] for r in results)
        print(f"{m:12s} {w}/{len(results)} won  avg margin {sum(r[1] for r in results) / len(results):+7.0f} gems"
              f"  avg rounds {sum(r[2] for r in results) / len(results):5.0f}")
    lo, hi = wilson(wins, games)
    print(f"\n{bot_a.name} vs {bot_b.name}: {wins}/{games} = {wins / max(games, 1):.0%} "
          f"(95% CI {lo:.0%}-{hi:.0%}), {bot_a.name} faults {faults}, failed matches {failed}")
    if args.min_winrate is not None and wins / max(games, 1) < args.min_winrate:
        sys.exit(1)


if __name__ == "__main__":
    main()
