#!/usr/bin/env python3
"""Group our ranked opponents by play style and show our record against each style (Phase 2 item 12; stdlib).

    python3 tools/styles.py replays/daniel-v8 replays/daniel-v9 replays/daniel-v10 [--k 4]

Each opponent in features.jsonl (tools/ranked.py) is described by its draft (one-hot per champion), the share of
its shards in each emblem family, its kills per game, and its gem lead at round 500. Features are standardised,
then grouped by k-means (k-means++ start, best of 10 runs). Prints, per style: size, our win rate, the champions and
shard families that set it apart (largest mean z), and the maps where we meet it most.
"""
import argparse
import collections
import json
import math
import random
from pathlib import Path

CHAMPS = ["Ryth", "Vesper Vale", "Vendetta", "Cassi", "Stellar", "Prism", "Marcella", "Willow", "Ren", "Varg", "Tavi",
          "Heart of Ruin"]
FAMILIES = ["monster", "power", "durability", "treasure", "jungle", "home", "bruiser"]


def vector(r):
    picks = set(r.get("their_picks", []))
    shards = r.get("their_shards", {})
    total = sum(shards.values()) or 1
    lead = (r.get("their_gems_r500", 0) or 0) - (r.get("gems_r500", 0) or 0)
    return ([1.0 if c in picks else 0.0 for c in CHAMPS] + [shards.get(f, 0) / total for f in FAMILIES]
            + [float(r.get("their_kills", 0)), float(lead)])


NAMES = [f"pick:{c}" for c in CHAMPS] + [f"shard:{f}" for f in FAMILIES] + ["kills", "gem_lead_r500"]


def kmeans(xs, k, rng, iters=50):
    centres = [rng.choice(xs)]
    while len(centres) < k:
        d = [min(sum((a - b) ** 2 for a, b in zip(x, c)) for c in centres) for x in xs]
        centres.append(rng.choices(xs, weights=d)[0])
    for _ in range(iters):
        labels = [min(range(k), key=lambda j: sum((a - b) ** 2 for a, b in zip(x, centres[j]))) for x in xs]
        for j in range(k):
            members = [x for x, l in zip(xs, labels) if l == j]
            if members:
                centres[j] = [sum(col) / len(members) for col in zip(*members)]
    cost = sum(sum((a - b) ** 2 for a, b in zip(x, centres[l])) for x, l in zip(xs, labels))
    return labels, cost


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dirs", nargs="+")
    parser.add_argument("--k", type=int, default=4)
    args = parser.parse_args()
    rows = []
    for d in args.dirs:
        path = Path(d) / "features.jsonl"
        if path.exists():
            rows += [json.loads(line) | {"version": Path(d).name} for line in path.read_text().splitlines() if line.strip()]
    raw = [vector(r) for r in rows]
    means = [sum(c) / len(raw) for c in zip(*raw)]
    sds = [math.sqrt(sum((v - m) ** 2 for v in c) / len(raw)) or 1.0 for c, m in zip(zip(*raw), means)]
    xs = [[(v - m) / s for v, m, s in zip(x, means, sds)] for x in raw]
    rng = random.Random(0)
    labels, _ = min((kmeans(xs, args.k, rng) for _ in range(10)), key=lambda t: t[1])

    print(f"{len(rows)} ranked games from {', '.join(args.dirs)}; overall win rate "
          f"{sum(r['win'] for r in rows) / len(rows):.0%}\n")
    for j in sorted(set(labels), key=lambda j: sum(rows[i]["win"] for i in range(len(rows)) if labels[i] == j)
                    / max(1, labels.count(j))):
        members = [i for i in range(len(rows)) if labels[i] == j]
        wins = sum(rows[i]["win"] for i in members)
        centre = [sum(xs[i][f] for i in members) / len(members) for f in range(len(NAMES))]
        traits = sorted(range(len(NAMES)), key=lambda f: -abs(centre[f]))[:5]
        maps = collections.Counter(rows[i]["map"] for i in members).most_common(3)
        print(f"style {j}: {len(members)} games, we win {wins}/{len(members)} = {wins / len(members):.0%}")
        print("   traits: " + ", ".join(f"{NAMES[f]} {centre[f]:+.1f}σ" for f in traits))
        print("   most common maps: " + ", ".join(f"{m} ({n})" for m, n in maps))


if __name__ == "__main__":
    main()
