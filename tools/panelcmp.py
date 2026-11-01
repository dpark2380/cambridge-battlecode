#!/usr/bin/env python3
"""Paired comparison of two scrim-panel versions (stdlib only; docs/research/process-review-2026-11-01.md §1.4-1.6).

    python3 tools/panelcmp.py v47 v48          # candidate v48 against base v47

Games are paired by (opponent, map, side); the panel is deterministic per setup, so a pair differs only by our bot.
Rows are rebuilt from data/scrims/<version>/summaries with features.row(), so older features.jsonl need no rebuild.
Prints W-L and net flips, then per metric the base mean, candidate mean and paired delta +- SE (candidate - base).
Verdict rule (§1.6): better if delta margin >= +2 SE, or delta deaths <= -2 SE with delta margin >= 0; worse if
delta margin <= -2 SE; otherwise neutral. Net W-L flips inside +-9 are not evidence.
"""
import json
import math
import sys
from pathlib import Path

import features

DIR = Path(__file__).resolve().parent.parent / "data" / "scrims"
METRICS = [  # (label, function of row)
    ("gem margin", lambda r: r["gems"] - r["their_gems"]),
    ("gems", lambda r: r["gems"]),
    ("gems r500", lambda r: r.get("gems_r500", 0)),
    ("deaths", lambda r: r["deaths"]),
    ("kills", lambda r: r["kills"]),
    ("gold", lambda r: r["earnedGold"]),
    ("gold/clear", lambda r: r["earnedGold"] / max(1, r["camp_clears"])),
    ("captures", lambda r: r["captures"]),
    ("gems captured", lambda r: r["gems_captured"]),
    ("gems/capture", lambda r: r["gems_captured"] / max(1, r["captures"])),
    ("gems lost to champs", lambda r: r["gems_lost_to_champions"]),
    ("bags", lambda r: r["bags"]),
    ("bag median", lambda r: r["bag_median"]),
    ("first emblem", lambda r: r["first_emblem"] or 2000),
    ("emblems r200", lambda r: r["emblems_r200"]),
    ("shop visits", lambda r: r["shop_visits"]),
    ("champ dmg done", lambda r: r["championDamageDone"]),
    ("champ dmg taken", lambda r: r["championDamageTaken"]),
    ("mob dmg done/taken", lambda r: r["monsterDamageDone"] / max(1, r["monsterDamageTaken"])),
    ("their gold", lambda r: r["their_earnedGold"]),
    ("their deaths", lambda r: r["their_deaths"]),
]


def rows(version):
    out = {}
    for line in (DIR / version / "features.jsonl").read_text().splitlines():
        r = json.loads(line)
        path = DIR / version / "summaries" / f"{r['match']}.json.gz"
        if not path.exists():
            continue
        full = features.row(features.load(path), r["side"], r["match"], r["map"], r["win"])
        out[(r["team"], r["map"], r["side"])] = full
    return out


def main():
    base, cand = sys.argv[1], sys.argv[2]
    a, b = rows(base), rows(cand)
    keys = sorted(set(a) & set(b))
    print(f"{cand} vs {base}: {len(keys)} paired games (base {len(a)}, candidate {len(b)})")
    wa, wb = sum(a[k]["win"] for k in keys), sum(b[k]["win"] for k in keys)
    flips = sum((b[k]["win"] != a[k]["win"]) for k in keys)
    print(f"  wins {wa} -> {wb} (net {wb - wa:+d}, {flips} flipped, {len(keys) - flips} identical outcome)")
    print(f"  {'metric':22s} {'base':>9s} {'cand':>9s} {'delta':>9s} {'SE':>7s}  z")
    verdict = {}
    for label, f in METRICS:
        d = [f(b[k]) - f(a[k]) for k in keys]
        n = len(d)
        mean = sum(d) / n
        sd = math.sqrt(sum((x - mean) ** 2 for x in d) / max(1, n - 1))
        se = sd / math.sqrt(n)
        z = mean / se if se else 0
        ma, mb = sum(f(a[k]) for k in keys) / n, sum(f(b[k]) for k in keys) / n
        flag = " **" if abs(z) >= 2 else ""
        print(f"  {label:22s} {ma:9.2f} {mb:9.2f} {mean:+9.2f} {se:7.2f} {z:+5.1f}{flag}")
        verdict[label] = (mean, se)
    m, ms = verdict["gem margin"]
    dd, ds = verdict["deaths"]
    if ms and m >= 2 * ms or (ds and dd <= -2 * ds and m >= 0):
        print("verdict: BETTER")
    elif ms and m <= -2 * ms:
        print("verdict: WORSE")
    else:
        print("verdict: neutral (stack it; no verdict on W-L flips inside +-9)")


if __name__ == "__main__":
    main()
