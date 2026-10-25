#!/usr/bin/env python3
"""Tune a bot's named constants by self-play: a simple evolution strategy against the incumbent.

    python3 tools/tune.py --bot v4 --params recall_health,tribute_gems,engage_radius --iterations 15
    python3 tools/tune.py --bot main-cpp --iterations 20          # bots with src/params.h: all P(...) entries

Constants are found by name in --file (default src/params.h if present, else src/bot.cpp) as `name = 1.5f` or
`P(name, 1.5f)`; integer literals stay integers, and values in (0, 1) stay in (0.02, 0.98). Each iteration
perturbs the incumbent into --candidates variants (log-normal steps), builds each as a copy under bots/_tune*/,
and plays it against the incumbent on every map x --seeds random drafts x both sides. A candidate replaces the
incumbent only if it wins at least --accept of those games and then again on fresh seeds (T7: the best of several
noisy candidates is biased upwards). Random drafts come from the bot's fuel-seed hook
(see draft.cpp), so every game is distinct; a bot without the hook just replays its own draft.
"""
import argparse
import json
import math
import random
import re
import shutil
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena  # noqa: E402

ROOT = arena.ROOT
LOG = ROOT / "data" / "tune_log.jsonl"
NUMBER = r"(-?[0-9]+(?:\.[0-9]*)?)(f?)"


def pattern(name):
    # `name = 1.5f` (constexpr) or `P(name, 1.5f)` (params.h macro list); first occurrence wins.
    return re.compile(rf"\b({name}\s*(?:=|,)\s*){NUMBER}")


def read_params(path, names=None):
    """{name: (value, is_int)} for the given names, or every P(...) entry when names is None."""
    text = path.read_text()
    names = names or re.findall(r"\bP\((\w+), -?[0-9]", text)
    out = {}
    for name in names:
        m = pattern(name).search(text)
        if not m:
            sys.exit(f"{name} not found in {path}")
        out[name] = (float(m.group(2)), "." not in m.group(2))
    return out


def write_params(values, path):
    text = path.read_text()
    for name, (value, is_int) in values.items():
        literal = str(round(value)) if is_int else f"{value:.4f}"
        text = pattern(name).sub(lambda m: m.group(1) + literal + m.group(3), text, count=1)
    path.write_text(text)


def make_bot(source, rel_file, name, values):
    """Copy `source` to bots/<name> with these values and build it."""
    path = ROOT / "bots" / name
    shutil.rmtree(path, ignore_errors=True)
    shutil.copytree(source, path, ignore=shutil.ignore_patterns(".cambc", "build", "compile_commands.json"))
    write_params(values, path / rel_file)
    arena.build(path)
    return path


def perturb(values, sigma, rng):
    out = {}
    for name, (v, is_int) in values.items():
        new = v * math.exp(rng.gauss(0, sigma)) if v > 0 else v + rng.gauss(0, sigma)
        if 0 < v < 1:
            new = min(0.98, max(0.02, new))
        if is_int and round(new) == round(v) and rng.random() < 0.5:
            new = v + rng.choice((-1, 1))  # small ints would otherwise rarely move
        out[name] = (max(new, 1) if is_int and v >= 1 else new, is_int)
    return out


def duel(bot_a, bot_b, seeds, jobs):
    """Paired games on every map and seed, both sides; return (A's win rate, A's mean gem margin).
    Uses arena.run_matches, so bots with experiment_seed.h play seeded copies at 100k fuel."""
    results = [arena.a_result(a_first, stats)
               for _, a_first, stats in arena.run_matches(bot_a, bot_b, arena.maps(), repeat=0, jobs=jobs, seeds=seeds)
               if stats]
    wins = sum(r[0] for r in results)
    return wins / max(len(results), 1), sum(r[1] for r in results) / max(len(results), 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--bot", default="main-cpp")
    parser.add_argument("--file", default=None, help="file holding the constants, relative to the bot")
    parser.add_argument("--params", default=None, help="comma-separated constant names (default: all P(...) entries)")
    parser.add_argument("--iterations", type=int, default=10)
    parser.add_argument("--candidates", type=int, default=3)
    parser.add_argument("--seeds", type=int, default=2, help="random drafts per map per duel")
    parser.add_argument("--sigma", type=float, default=0.25, help="log-normal step size")
    parser.add_argument("--accept", type=float, default=0.56, help="win rate a candidate needs to replace the incumbent")
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--rng", type=int, default=int(time.time()))
    parser.add_argument("--apply", action="store_true", help="write the final values back into the bot")
    args = parser.parse_args()

    source = arena.bot_path(args.bot)
    rel_file = Path(args.file) if args.file else Path("src/params.h") if (source / "src/params.h").exists() else Path("src/bot.cpp")
    names = args.params.split(",") if args.params else None
    rng = random.Random(args.rng)
    best = read_params(source / rel_file, names)
    incumbent = make_bot(source, rel_file, "_tune_best", best)
    LOG.parent.mkdir(exist_ok=True)
    show = lambda values: json.dumps({k: round(v, 3) for k, (v, _) in values.items()})
    print("start", show(best), flush=True)

    for it in range(args.iterations):
        seeds = [rng.randrange(1, 400) for _ in range(args.seeds)]  # fresh drafts every iteration
        scored = []
        for i in range(args.candidates):
            values = perturb(best, args.sigma, rng)
            bot = make_bot(source, rel_file, f"_tune_{i}", values)
            rate, margin = duel(bot, incumbent, seeds, args.jobs)
            scored.append((rate, margin, values))
            print(f"iter {it} cand {i}: win {rate:.0%} margin {margin:+.0f}", flush=True)
        rate, margin, values = max(scored, key=lambda s: (s[0], s[1]))
        accepted = rate >= args.accept
        if accepted:
            # T7: the best of several candidates is biased upwards (three 50% candidates pass a 56% bar ~18% of
            # the time), so the winner must pass again on fresh seeds.
            confirm_seeds = [rng.randrange(400, 800) for _ in range(args.seeds)]
            bot = make_bot(source, rel_file, "_tune_confirm", values)
            confirm, _ = duel(bot, incumbent, confirm_seeds, args.jobs)
            print(f"iter {it}: best {rate:.0%}, confirmation on fresh seeds {confirm:.0%}", flush=True)
            accepted = confirm >= args.accept
        with LOG.open("a") as log:
            log.write(json.dumps({"bot": args.bot, "iter": it, "rate": rate, "margin": margin, "accepted": accepted,
                                  "params": {k: v for k, (v, _) in values.items()}}) + "\n")
        if accepted:
            best = values
            incumbent = make_bot(source, rel_file, "_tune_best", best)
            print(f"iter {it}: accepted ({rate:.0%})", show(best), flush=True)

    for i in range(args.candidates):
        shutil.rmtree(ROOT / "bots" / f"_tune_{i}", ignore_errors=True)
    shutil.rmtree(ROOT / "bots" / "_tune_confirm", ignore_errors=True)
    print("best", show(best))
    if args.apply:
        write_params(best, source / rel_file)
        print(f"wrote {(source / rel_file).relative_to(ROOT)}")


if __name__ == "__main__":
    main()
