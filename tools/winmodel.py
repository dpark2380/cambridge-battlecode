#!/usr/bin/env python3
"""Win-probability model from match summaries (Phase 2 item 8; stdlib only).

    python3 tools/winmodel.py                                     # fit on every full summary we have
    python3 tools/winmodel.py --ours replays/daniel-v10           # + when each of our losses was decided

Input: full summaries (`events` + per-round timelines): replays/*/summaries/*.json.gz (ours) and
data/scout/summaries/*.json.gz (top teams, saved by tools/scout.py). Every 100 rounds, each game gives one state
per side: the difference between the two teams in submitted gems, carried gems, gold earned, kills, deaths and
monster damage (Erickson & Buro, AIIDE 2014). Each state is added once from each side with the label flipped,
which removes side bias. One logistic regression per phase of the game (rounds 100-500, 600-1000, 1100-2000),
fitted by gradient descent on standardised features. Accuracy comes from 5-fold cross-validation grouped by game.

Prints the accuracy per phase; the weights as trade-offs (how many submitted gems one unit of each feature is
worth); and with --ours, the "collapse round" of each of our losses (the first round from which our win
probability stays below 0.3), which says which part of a replay to watch.
"""
import argparse
import glob
import json
import math
import random
from pathlib import Path

import features

ROOT = Path(__file__).resolve().parent.parent
PHASES = [(100, 500), (600, 1000), (1100, 2000)]
# (feature, championTimelines metric or None for team submitted gems)
FEATURES = [("submitted", None), ("carried", "gems"), ("gold", "earnedGold"), ("kills", "kills"),
            ("deaths", "deaths"), ("monster_dmg", "monsterDamageDone")]


def team_totals(summary, round_):
    """{team: {feature: value at round_}}."""
    out = {"teamA": dict.fromkeys([f for f, _ in FEATURES], 0.0), "teamB": dict.fromkeys([f for f, _ in FEATURES], 0.0)}
    for t in summary.get("teamTimelines", []):
        if t["metric"] == "submittedGems":
            out[t["owner"]]["submitted"] = features.at_round(t["runs"], round_)
    metric_to_feature = {m: f for f, m in FEATURES if m}
    for t in summary.get("championTimelines", []):
        feature = metric_to_feature.get(t["metric"])
        if feature:
            out[t["owner"]["team"]][feature] += features.at_round(t["runs"], round_)
    return out


def states(summary):
    """[(round, diff vector A-B, A won)] every 100 rounds while the game lasted."""
    if "championTimelines" not in summary:
        return []
    winner = summary["match"]["outcome"]
    if winner not in ("teamA", "teamB"):
        return []
    rows = []
    for r in range(100, summary["match"]["roundsCompleted"] + 1, 100):
        tot = team_totals(summary, r)
        rows.append((r, [tot["teamA"][f] - tot["teamB"][f] for f, _ in FEATURES], winner == "teamA"))
    return rows


def fit(xs, ys, epochs=300, lr=0.5, l2=1e-3):
    """Logistic regression by batch gradient descent; returns (weights, bias, means, scales)."""
    n, d = len(xs), len(xs[0])
    means = [sum(x[j] for x in xs) / n for j in range(d)]
    scales = [math.sqrt(sum((x[j] - means[j]) ** 2 for x in xs) / n) or 1.0 for j in range(d)]
    z = [[(x[j] - means[j]) / scales[j] for j in range(d)] for x in xs]
    w, b = [0.0] * d, 0.0
    for _ in range(epochs):
        gw, gb = [0.0] * d, 0.0
        for x, y in zip(z, ys):
            p = 1 / (1 + math.exp(-max(-30, min(30, b + sum(wj * xj for wj, xj in zip(w, x))))))
            e = p - y
            gb += e
            for j in range(d):
                gw[j] += e * x[j]
        b -= lr * gb / n
        w = [wj - lr * (gj / n + l2 * wj) for wj, gj in zip(w, gw)]
    return w, b, means, scales


def predict(model, x):
    w, b, means, scales = model
    s = b + sum(wj * (xj - m) / sc for wj, xj, m, sc in zip(w, x, means, scales))
    return 1 / (1 + math.exp(-max(-30, min(30, s))))


def samples(games, phase):
    xs, ys, ids = [], [], []
    for gid, rows in games.items():
        for r, diff, a_won in rows:
            if phase[0] <= r <= phase[1]:
                xs += [diff, [-v for v in diff]]
                ys += [1.0 if a_won else 0.0, 0.0 if a_won else 1.0]
                ids += [gid, gid]
    return xs, ys, ids


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ours", help="a replays/<version> folder: report the collapse round of its losses")
    parser.add_argument("--team", default="Deer Park")
    args = parser.parse_args()

    paths = glob.glob(str(ROOT / "replays/*/summaries/*.json.gz")) + glob.glob(str(ROOT / "data/scout/summaries/*.json.gz"))
    games = {}
    for p in paths:
        rows = states(features.load(p))
        if rows:
            games[Path(p).name.split(".")[0]] = rows
    print(f"{len(games)} games with per-round timelines")

    models = {}
    rng = random.Random(0)
    ids_all = sorted(games)
    rng.shuffle(ids_all)
    folds = {g: i % 5 for i, g in enumerate(ids_all)}
    print("\nheld-out accuracy by phase (5-fold, grouped by game):")
    for phase in PHASES:
        xs, ys, ids = samples(games, phase)
        if len(xs) < 50:
            continue
        correct = total = 0
        for k in range(5):
            train = [i for i, g in enumerate(ids) if folds[g] != k]
            test = [i for i, g in enumerate(ids) if folds[g] == k]
            model = fit([xs[i] for i in train], [ys[i] for i in train])
            correct += sum((predict(model, xs[i]) > 0.5) == (ys[i] > 0.5) for i in test)
            total += len(test)
        models[phase] = fit(xs, ys)
        print(f"  rounds {phase[0]:4d}-{phase[1]:4d}: {correct / max(total, 1):.1%} over {total // 2} states")

    print("\ntrade-offs: value of one unit of each feature in submitted gems (raw-unit weight / gem weight):")
    names = [f for f, _ in FEATURES]
    for phase, (w, b, means, scales) in models.items():
        raw = [wj / sc for wj, sc in zip(w, scales)]
        gem = raw[0] or 1e-9
        print(f"  {phase[0]:4d}-{phase[1]:4d}: " + ", ".join(f"{n} {r / gem:+.3f}" for n, r in zip(names, raw)))

    if args.ours:
        out = Path(args.ours)
        matches = {m["matchId"]: m for m in json.loads((out / "matches.json").read_text())}
        print(f"\ncollapse round of our losses in {out} (our win probability stays below 0.3 from then on):")
        for mid, m in matches.items():
            us = next(t for t in m["teams"] if t["name"] == args.team)
            path = out / "summaries" / f"{mid}.json.gz"
            if us["result"] == "win" or not path.exists() or mid not in games:
                continue
            sign = 1 if us["side"] == "a" else -1
            curve = []
            for r, diff, _ in games[mid]:
                phase = next((ph for ph in models if ph[0] <= r <= ph[1]), None)
                if phase:
                    curve.append((r, predict(models[phase], [sign * v for v in diff])))
            collapse = next((r for i, (r, _) in enumerate(curve) if all(p < 0.3 for _, p in curve[i:])), None)
            print(f"  {m['map']:22s} collapse r{collapse}  " + " ".join(f"{p:.2f}" for _, p in curve[::3]))


if __name__ == "__main__":
    main()
