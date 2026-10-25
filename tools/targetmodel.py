#!/usr/bin/env python3
"""Which camp group does a champion take next? A choice model fitted on top-team play and on ours (B26; stdlib).

    python3 tools/targetmodel.py [--ours replays/daniel-v10 replays/daniel-v9] [--export]

Every campClear event in a full summary names the champion, the group and the round. The decision point for a
clear is the champion's last event before it: its previous clear, a gem submission (at an altar), or its death
(it respawns at its spawn); for the first clear, round 0 at its spawn. The candidates are all groups on the map, described by features the bot can compute in game:

    gems, gold          log1p of the group's reward (maps/ascii)
    dist                log1p of the walking distance from the decision point (BFS on the map dump)
    altar               log1p of the walking distance from the group to the nearest altar
    threat              log1p of the group's monster strength (wolf 1, elk 2, golem 3, monolith 8)
    up                  1 if nobody cleared it in the respawn window before the decision (else it is respawning)
    again               1 if it is the group this champion just cleared
    own_side            1 if the group is nearer our spawn than theirs
    late_gems           gems x (round >= 500)

A conditional logit (softmax over the candidates) is fitted separately to top-20 decisions (data/scout/summaries)
and to ours (--ours folders), so the weights can be compared. Held-out top-1 accuracy is printed next to the
"nearest available group" baseline. --export writes the top-team weights as a C++ table to
data/targetmodel-weights.txt.
"""
import argparse
import collections
import glob
import gzip
import json
import math
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ["gems", "gold", "dist", "altar", "threat", "up", "again", "own_side", "late_gems"]
STRENGTH = {"w": 1, "k": 2, "G": 3, "M": 8}


def load_map(name):
    path = ROOT / "maps" / "ascii" / f"{name.replace('_', '-')}.txt"
    if not path.exists():
        return None
    text = path.read_text()
    grid = [m.group(1) for m in re.finditer(r"^\s*\d+  (\S+)$", text, re.M)]
    groups = {}
    for m in re.finditer(r"# G(\d+) (\{.*?\}) gems=(\d+) gold=(\d+) respawn=(\d+) at=\((\d+),(\d+)\)", text):
        comp = eval(m.group(2), {})  # dict literal written by tools/dump_maps.py
        groups[int(m.group(1))] = dict(gems=int(m.group(3)), gold=int(m.group(4)), respawn=int(m.group(5)),
                                       at=(int(m.group(6)), int(m.group(7))),
                                       threat=sum(STRENGTH.get(k, 0) * v for k, v in comp.items()))
    tiles = {c: [(x, y) for y, row in enumerate(grid) for x, ch in enumerate(row) if ch == c] for c in "SEA"}
    return dict(grid=grid, groups=groups, spawn={"A": tiles["S"], "B": tiles["E"]}, altars=tiles["A"])


def bfs(grid, sources):
    h, w = len(grid), len(grid[0])
    dist = {s: 0 for s in sources}
    queue = collections.deque(sources)
    while queue:
        x, y = queue.popleft()
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                nx, ny = x + dx, y + dy
                if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in dist and grid[ny][nx] not in "#o":
                    dist[(nx, ny)] = dist[(x, y)] + 1
                    queue.append((nx, ny))
    return dist


class MapCache:
    def __init__(self):
        self.maps = {}

    def get(self, name):
        if name not in self.maps:
            m = load_map(name)
            if m:
                m["from"] = {g: bfs(m["grid"], [info["at"]]) for g, info in m["groups"].items()}
                far = 4 * (len(m["grid"]) + len(m["grid"][0]))
                for g, info in m["groups"].items():
                    d = m["from"][g]
                    info["altar"] = min((d.get(a, far) for a in m["altars"]), default=far)
                    info["spawn"] = {t: min((d.get(s, far) for s in m["spawn"][t]), default=far) for t in "AB"}
                m["far"] = far
            self.maps[name] = m
        return self.maps[name]


def decisions(summary, m, side_filter):
    """Yield (candidate feature rows, chosen index) for each clear by a champion of a team in side_filter.

    The decision point is the champion's last event before the clear: its previous clear, a gem submission (at an
    altar) or its death (it respawns at its spawn)."""
    timeline = collections.defaultdict(list)  # champion -> [(round, kind, group, (x, y))]
    every = collections.defaultdict(list)     # group -> rounds cleared (by anyone)
    for e in summary.get("events", []):
        if e["kind"] not in ("campClear", "gemSubmission", "death"):
            continue
        owner = e["owner"]
        if owner.get("kind") != "champion":
            continue
        for entry in e["entries"]:
            r = entry["timestamp"]["round"]
            g = entry["target"]["id"] if e["kind"] == "campClear" else None
            if g is not None:
                every[g].append(r)
            timeline[(owner["team"], owner["id"])].append((r, e["kind"], g, (entry["x"], entry["y"])))
    for (team, _), seq in timeline.items():
        side = team[-1]
        if side not in side_filter:
            continue
        seq.sort(key=lambda t: t[0])
        spawn = m["spawn"][side]
        start = (sum(p[0] for p in spawn) // max(1, len(spawn)), sum(p[1] for p in spawn) // max(1, len(spawn)))
        prev_round, prev_pos, prev_group = 0, start, None
        for r, kind, g, pos in seq:
            if kind == "gemSubmission":
                prev_round, prev_pos = r, pos
                continue
            if kind == "death":
                prev_round, prev_pos = r, start
                continue
            if g not in m["groups"]:
                break
            rows, chosen = [], None
            for cand, info in m["groups"].items():
                d = m["from"][cand].get(prev_pos, m["far"])
                up = not any(prev_round - info["respawn"] < t <= prev_round for t in every[cand])
                own = info["spawn"][side] < info["spawn"]["B" if side == "A" else "A"]
                rows.append([math.log1p(info["gems"]), math.log1p(info["gold"]), math.log1p(d), math.log1p(info["altar"]),
                             math.log1p(info["threat"]), float(up), float(cand == prev_group), float(own),
                             math.log1p(info["gems"]) * (prev_round >= 500)])
                if cand == g:
                    chosen = len(rows) - 1
            yield rows, chosen
            prev_round, prev_pos, prev_group = r, pos, g


def loglik(w, data):
    total = 0.0
    for rows, chosen in data:
        scores = [sum(a * b for a, b in zip(w, f)) for f in rows]
        top = max(scores)
        total += scores[chosen] - top - math.log(sum(math.exp(s - top) for s in scores))
    return total / max(1, len(data))


def fit(data, l2=0.001, epochs=12, lr=0.02):
    """Stochastic gradient ascent on the conditional-logit likelihood, step size decaying per epoch."""
    w = [0.0] * len(FEATURES)
    data = list(data)
    for epoch in range(epochs):
        random.shuffle(data)
        step = lr / (1 + epoch)
        for rows, chosen in data:
            scores = [sum(a * b for a, b in zip(w, f)) for f in rows]
            top = max(scores)
            ps = [math.exp(s - top) for s in scores]
            z = sum(ps)
            grad = [rows[chosen][j] - sum(p * f[j] for p, f in zip(ps, rows)) / z for j in range(len(w))]
            w = [wj + step * (gj - l2 * wj) for wj, gj in zip(w, grad)]
    return w


def accuracy(w, data):
    hit = near = 0
    for rows, chosen in data:
        hit += max(range(len(rows)), key=lambda i: sum(a * b for a, b in zip(w, rows[i]))) == chosen
        near += min((i for i in range(len(rows)) if rows[i][5]), key=lambda i: rows[i][2], default=-1) == chosen
    return hit / max(1, len(data)), near / max(1, len(data))


def collect(items, maps):
    out = []
    for path, map_name, sides in items:
        m = maps.get(map_name)
        if not m or not Path(path).exists():
            continue
        s = json.load(gzip.open(path)) if str(path).endswith(".gz") else json.load(open(path))
        out += [(rows, c) for rows, c in decisions(s, m, sides) if c is not None]
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ours", nargs="*", default=[])
    parser.add_argument("--team", default="Deer Park")
    parser.add_argument("--export", action="store_true")
    args = parser.parse_args()
    random.seed(0)
    maps = MapCache()

    top = {}
    for tally in glob.glob(str(ROOT / "data" / "scout" / "2*.json")):
        for e in json.loads(Path(tally).read_text()):
            for g in e["games"]:
                top[g["match"]] = (g["map"], g["side"].upper())
    top_items = [(ROOT / "data" / "scout" / "summaries" / f"{mid}.json.gz", m, s) for mid, (m, s) in top.items()]
    our_items = []
    for folder in args.ours:
        for match in json.loads((Path(folder) / "matches.json").read_text()):
            us = next(t for t in match["teams"] if t["name"] == args.team)
            our_items.append((Path(folder) / "summaries" / f"{match['matchId']}.json.gz", match["map"], us["side"].upper()))

    for label, items in (("top 20", top_items), ("ours", our_items)):
        data = collect(items, maps)
        if not data:
            continue
        random.shuffle(data)
        cut = len(data) * 4 // 5
        w = fit(data[:cut])
        acc, near = accuracy(w, data[cut:])
        print(f"\n{label}: {len(data)} decisions; held-out top-1 {acc:.0%} (nearest available group {near:.0%}); "
              f"held-out log-likelihood {loglik(w, data[cut:]):.3f} vs uniform {loglik([0.0] * len(w), data[cut:]):.3f}")
        for name, value in zip(FEATURES, w):
            print(f"  {name:10s} {value:+.2f}")
        if label == "top 20" and args.export:
            (ROOT / "data" / "targetmodel-weights.txt").write_text(
                "\n".join(f"{n} {v:.4f}" for n, v in zip(FEATURES, fit(data))) + "\n")


if __name__ == "__main__":
    main()
