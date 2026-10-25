#!/usr/bin/env python3
"""One compact feature row per match summary, plus rule-based loss signatures (stdlib only).

    python3 tools/features.py replays/daniel-v9            # rebuild <dir>/features.jsonl from <dir>/summaries/
    python3 tools/features.py replays/daniel-v9 --table    # also print signature counts per map (losses)

A full summary (`cambc matches summary --json`) holds `events` (deaths with the killer, gem losses, camp clears,
item buys, fuelExhausted, botFault: each with round and x, y) and `teamTimelines` (submitted gems per round).
ranked.py keeps them gzipped and calls row() for every game. Rows from stripped summaries (before 2026-10-25)
lack the event fields. Signatures (a loss can carry several):
  frozen       we bank < 100 gems with < 15 deaths: the bot stalls, not fights (01the_farm in v8)
  tiebreak     the game reaches round 2000 with both teams below 1000
  race         they reach 1000 first without out-killing us: they farm faster
  spiral       we die at least twice as often as they do, 30+ times
  camp_trap    15+ deaths to camps, half or more of ours, at one hotspot (x, y in 4x4 cells)
  fuel         20+ fuelExhausted turns after round 1 on our side
  fault        any bot fault on our side
"""
import argparse
import collections
import gzip
import json
from pathlib import Path


def load(path):
    path = Path(path)
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt") as f:
        return json.load(f)


def at_round(runs, round_):
    """Value of a run-length timeline (list of {duration, value}) at `round_`."""
    t, value = 0, 0.0
    for run in runs:
        if t > round_:
            break
        value = float(run["value"])
        t += int(run["duration"])
    return value


def row(summary, ours, match_id="", map_name="", won=None):
    """Feature dict for one match from team `ours` ('teamA' or 'teamB')."""
    theirs = "teamB" if ours == "teamA" else "teamA"
    gems = {t["team"]: int(t["submittedGems"]) for t in summary["teams"]}
    rounds = summary["match"]["roundsCompleted"]
    if won is None:
        won = summary["match"]["outcome"] == ours
    r = {"match": match_id, "map": map_name, "side": ours, "win": won, "rounds": rounds,
         "gems": gems[ours], "their_gems": gems[theirs]}
    for side, prefix in ((ours, ""), (theirs, "their_")):
        champs = [c for c in summary["champions"] if c["team"] == side]
        for metric in ("deaths", "kills", "earnedGold", "monsterDamageTaken", "championDamageTaken"):
            r[prefix + metric] = round(sum(float(c["metrics"][metric]) for c in champs))
        shards = collections.Counter()
        for c in champs:
            for item in c.get("itemsBought", []):  # emblems are listed too, but every shard bought is counted
                if " Shard " in item["item"]:
                    shards[item["item"].split()[0].lower()] += int(item["quantity"])
        r[prefix + "shards"] = dict(shards)
        r[prefix + "picks"] = sorted(c["name"] for c in champs)
    for t in summary.get("teamTimelines", []):
        if t["metric"] == "submittedGems":
            prefix = "" if t["owner"] == ours else "their_"
            for checkpoint in (250, 500, 1000):
                r[f"{prefix}gems_r{checkpoint}"] = at_round(t["runs"], checkpoint)
    events = summary.get("events")
    if events is not None:
        deaths_by = collections.Counter()
        hotspots = collections.Counter()
        fuel = clears = their_clears = 0
        first_clear = None
        faults = 0
        for e in events:
            mine = e["owner"].get("team") == ours
            for entry in e["entries"]:
                rnd = entry["timestamp"]["round"]
                if e["kind"] == "death" and mine:
                    killer = entry["context"] or "unknown"
                    deaths_by[killer] += 1
                    if killer != "champion":
                        hotspots[(entry["x"] // 4 * 4, entry["y"] // 4 * 4)] += 1
                elif e["kind"] == "fuelExhausted" and mine and rnd > 1:
                    fuel += 1
                elif e["kind"] == "botFault" and mine:
                    faults += 1
                elif e["kind"] == "campClear":
                    if mine:
                        clears += 1
                        first_clear = rnd if first_clear is None else min(first_clear, rnd)
                    else:
                        their_clears += 1
        r.update({"deaths_by": dict(deaths_by), "fuel_exhausted": fuel, "faults": faults, "camp_clears": clears,
                  "their_camp_clears": their_clears, "first_clear": first_clear,
                  "camp_hotspot": list(hotspots.most_common(1)[0][0]) if hotspots else None,
                  "camp_hotspot_deaths": hotspots.most_common(1)[0][1] if hotspots else 0})
    r["signatures"] = [] if won else signatures(r)
    return r


def signatures(r):
    sig = []
    if r["gems"] < 100 and r["deaths"] < 15:
        sig.append("frozen")
    if r["rounds"] >= 2000 and r["gems"] < 1000 and r["their_gems"] < 1000:
        sig.append("tiebreak")
    if r["their_gems"] >= 1000 and r["deaths"] <= r["their_deaths"] + 5:
        sig.append("race")
    if r["deaths"] >= 30 and r["deaths"] >= 2 * max(1, r["their_deaths"]):
        sig.append("spiral")
    if "deaths_by" in r:
        camp = sum(n for k, n in r["deaths_by"].items() if k != "champion")
        if camp >= 15 and camp * 2 >= r["deaths"] and r["camp_hotspot_deaths"] >= 8:
            sig.append("camp_trap")
        if r["fuel_exhausted"] >= 20:
            sig.append("fuel")
        if r["faults"]:
            sig.append("fault")
    return sig


def table(rows):
    """Signature counts per map over losses, worst maps first."""
    per_map = collections.defaultdict(collections.Counter)
    for r in rows:
        per_map[r["map"]]["games"] += 1
        if not r["win"]:
            per_map[r["map"]]["losses"] += 1
            per_map[r["map"]].update(r["signatures"])
    names = ["frozen", "tiebreak", "race", "spiral", "camp_trap", "fuel", "fault"]
    lines = [f"{'map':22s} {'W-L':>7s}  " + " ".join(f"{n:>9s}" for n in names)]
    for m, c in sorted(per_map.items(), key=lambda kv: -kv[1]["losses"] / kv[1]["games"]):
        lines.append(f"{m:22s} {c['games'] - c['losses']:>3d}-{c['losses']:<3d}  " + " ".join(f"{c[n]:>9d}" for n in names))
    total = collections.Counter()
    for c in per_map.values():
        total.update(c)
    lines.append(f"{'all':22s} {total['games'] - total['losses']:>3d}-{total['losses']:<3d}  " + " ".join(f"{total[n]:>9d}" for n in names))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("dir")
    parser.add_argument("--team", default="Deer Park")
    parser.add_argument("--table", action="store_true")
    args = parser.parse_args()
    out = Path(args.dir)
    matches = {m["matchId"]: m for m in json.loads((out / "matches.json").read_text())}
    rows = []
    for mid, m in matches.items():
        path = next((p for p in (out / "summaries" / f"{mid}.json.gz", out / "summaries" / f"{mid}.json") if p.exists()), None)
        if not path:
            continue
        us = next(t for t in m["teams"] if t["name"] == args.team)
        rows.append(row(load(path), "team" + us["side"].upper(), mid, m["map"], us["result"] == "win"))
    (out / "features.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    print(f"{len(rows)} rows -> {out / 'features.jsonl'}")
    if args.table:
        print(table(rows))


if __name__ == "__main__":
    main()
