#!/usr/bin/env python3
"""Learn draft values from self-play with random rosters.

    python3 tools/draft_lab.py collect --games 2000      # main-cpp mirror matches, random drafts
    python3 tools/draft_lab.py fit                       # print values, write bots/daniel/main-cpp/src/draft_table.h

`collect` runs the bot against itself with `--fuel 1000000 + 10000*seed`; the draft reads the seed from its
fuel budget and picks a random roster (bots/daniel/main-cpp/src/draft.cpp). Results append to data/draft_games.jsonl,
so collection can be resumed or extended.
Data goes to data/draft_games_<bot>.jsonl; `fit --bot X` reads it. Only main-cpp has a generated table (--no-write otherwise). `fit` regresses outcome on roster difference per team size:
logistic (win) and ridge (gem margin), both with L2, plain Python.
"""
import argparse
import json
import math
import random
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena  # noqa: E402

ROOT = arena.ROOT
TABLE = ROOT / "bots" / "daniel" / "main-cpp" / "src" / "draft_table.h"
NAMES = ["ryth", "vesper_vale", "vendetta", "cassi_and_issac", "stellar", "prism", "marcella", "willow", "ren",
         "varg", "tavi"]
SEEDS_PER_MAP = 400


def data_file(bot):
    """One file per bot: champion values depend on how the bot plays them."""
    return ROOT / "data" / f"draft_games_{Path(bot).name}.jsonl"


def load(bot="main-cpp"):
    path = data_file(bot)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def collect(args):
    # Play a frozen copy so edits to the source bot cannot change it mid-run.
    bot = ROOT / "bots" / "_tune_draftlab"
    shutil.rmtree(bot, ignore_errors=True)
    shutil.copytree(arena.bot_path(args.bot), bot, ignore=shutil.ignore_patterns(".cambc", "build", "compile_commands.json"))
    arena.build(bot)
    maps = arena.maps()
    done = {(g["map"], g["seed"]) for g in load(args.bot)}
    todo = [(m, seed) for seed in range(1, SEEDS_PER_MAP + 1) for m in maps if (m, seed) not in done][:args.games]
    data = data_file(args.bot)
    data.parent.mkdir(exist_ok=True)

    def one(job):
        m, seed = job
        stats = arena.play(bot, bot, m, fuel=arena.seed_fuel(seed))
        if stats is None:
            return None
        teams = stats["teams"]
        return {"map": m, "seed": seed, "picks": [teams[0]["draftPicks"], teams[1]["draftPicks"]],
                "gems": [teams[0]["submittedGems"], teams[1]["submittedGems"]],
                "winner": 0 if stats["outcome"] == "teamA" else 1, "round": stats["round"]}

    with ThreadPoolExecutor(args.jobs) as pool, data.open("a") as out:
        for i, row in enumerate(pool.map(one, todo), 1):
            if row:
                out.write(json.dumps(row) + "\n")
                out.flush()
            if i % 100 == 0:
                print(f"{i}/{len(todo)} games", flush=True)


def features(game):
    x = [0.0] * len(NAMES)
    for c in game["picks"][0]:
        x[c] += 1
    for c in game["picks"][1]:
        x[c] -= 1
    return x


def fit_logistic(rows, l2=1.0, steps=3000, lr=0.5):
    """Bradley-Terry: P(A wins) = sigmoid(bias + sum v_c x_c). Returns (values, bias)."""
    n = len(NAMES)
    w, b = [0.0] * n, 0.0
    for _ in range(steps):
        gw, gb = [l2 * wi / len(rows) for wi in w], 0.0
        for x, y in rows:
            p = 1 / (1 + math.exp(-(b + sum(wi * xi for wi, xi in zip(w, x)))))
            for i in range(n):
                gw[i] += (p - y) * x[i] / len(rows)
            gb += (p - y) / len(rows)
        w = [wi - lr * g for wi, g in zip(w, gw)]
        b -= lr * gb
    return w, b


def fit_ridge(rows, l2=1.0):
    """Least squares on gem margin / 1000 via normal equations (Gauss-Jordan)."""
    n = len(NAMES)
    a = [[l2 * (i == j) for j in range(n)] + [0.0] for i in range(n)]
    for x, y in rows:
        for i in range(n):
            for j in range(n):
                a[i][j] += x[i] * x[j]
            a[i][n] += x[i] * y
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(a[r][col]))
        a[col], a[pivot] = a[pivot], a[col]
        for r in range(n):
            if r != col and a[col][col]:
                f = a[r][col] / a[col][col]
                a[r] = [v - f * pv for v, pv in zip(a[r], a[col])]
    return [a[i][n] / a[i][i] for i in range(n)]


def fit(args):
    games = load(args.bot)
    if not games:
        sys.exit(f"no data in {data_file(args.bot)}; run collect first")
    random.seed(0)
    table = []
    print(f"{len(games)} games")
    for size in (3, 4, 5):
        subset = [g for g in games if len(g["picks"][0]) == size]
        if len(subset) < 50:
            print(f"team size {size}: only {len(subset)} games, using all sizes")
            subset = games
        win_rows = [(features(g), 1 - g["winner"]) for g in subset]
        margin_rows = [(features(g), (g["gems"][0] - g["gems"][1]) / 1000) for g in subset]
        # Hold out 20% to report how predictive the draft model is.
        random.shuffle(win_rows)
        cut = len(win_rows) // 5
        w, b = fit_logistic(win_rows[cut:], args.l2)
        hits = sum((b + sum(wi * xi for wi, xi in zip(w, x)) > 0) == (y == 1) for x, y in win_rows[:cut])
        w, b = fit_logistic(win_rows, args.l2)
        margin = fit_ridge(margin_rows, args.l2)
        print(f"\nteam size {size}: {len(subset)} games, held-out accuracy {hits / max(cut, 1):.0%}, side bias {b:+.2f}")
        for i in sorted(range(len(NAMES)), key=lambda i: -w[i]):
            print(f"  {NAMES[i]:16s} win logit {w[i]:+.2f}   gem margin {margin[i] * 1000:+5.0f}")
        table.append(w)

    if args.write:
        rows = ",\n".join("    {" + ", ".join(f"{v:.3f}f" for v in w) + "}" for w in table)
        TABLE.write_text(
            "#pragma once\n"
            "// Generated by tools/draft_lab.py fit. Value of each champion_draft per team size (3, 4, 5); higher picks first.\n"
            "// Order: " + ", ".join(NAMES) + ".\n"
            f"inline constexpr int kChampionCount = {len(NAMES)};\n"
            f"inline constexpr float kDraftValue[3][kChampionCount] = {{\n{rows},\n}};\n")
        print(f"\nwrote {TABLE.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("collect")
    c.add_argument("--games", type=int, default=900)
    c.add_argument("--jobs", type=int, default=8)
    c.add_argument("--bot", default="main-cpp")
    f = sub.add_parser("fit")
    f.add_argument("--bot", default="main-cpp")
    f.add_argument("--l2", type=float, default=1.0)
    f.add_argument("--no-write", dest="write", action="store_false")
    args = parser.parse_args()
    {"collect": collect, "fit": fit}[args.cmd](args)


if __name__ == "__main__":
    main()
