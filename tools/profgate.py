#!/usr/bin/env python3
"""Local panel against the profile bots (tools/profiles.py): each candidate plays every bots/_var/prof-* bot on the
scrim panel's maps, both sides (stdlib only; process review #9).

    python3 tools/profgate.py v51 v58                 # per-version mean gem margin, deaths, gold, win rate
    python3 tools/profgate.py v51 v58 --base v51      # also the paired delta of each version against the base
    python3 tools/profgate.py v51 v58 --base v51 --handicap 300   # candidates cannot shop before round 300

Games are deterministic per (version, profile, map, side), so versions are paired setup by setup, like panelcmp.py.
Calibrate before trusting it: the versions' order here should match their scrim-panel order.
"""
import argparse
import math
import shutil
import sys
from pathlib import Path

import arena
import scrim

ROOT = Path(__file__).resolve().parent.parent


def panel_maps():
    maps = []
    for names, _ in scrim.PANEL_MAPS:
        maps += [m.replace("_", "-") for m in names.split(",")]
    return maps


def handicapped(version, rounds):
    """A copy of the version that cannot shop before `rounds` (behind on shards, as we are in ranked: review §4)."""
    src = arena.bot_path(version)
    dst = ROOT / "bots" / "_var" / f"hc{rounds}-{src.name}"
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".cambc"))
    p = dst / "src" / "bot.cpp"
    s = p.read_text()
    anchor = "void Bot::shop() {\n"
    assert s.count(anchor) == 1, f"{version}: shop() anchor"
    p.write_text(s.replace(anchor, anchor + f"    if (cambc::round_number() < {rounds}) return;  // profgate handicap\n"))
    return dst


def play(version, profiles, maps, handicap=0):
    bot = handicapped(version, handicap) if handicap else arena.bot_path(version)
    arena.build(bot)
    rows = {}
    for prof in profiles:
        for m, a_first, stats in arena.run_matches(bot, prof, maps):
            if stats is None:
                continue
            won, margin, _ = arena.a_result(a_first, stats)
            d = arena.a_deltas(a_first, stats)
            a = 0 if a_first else 1
            rows[(prof.name, m, a_first)] = {"won": won, "margin": margin, "deaths": stats["teams"][a].get("deaths", 0),
                                             "gold": stats["teams"][a].get("earnedGold", 0),
                                             "captured": stats["teams"][a].get("gemsCaptured", 0), **{"d_" + k: v for k, v in d.items()}}
    return rows


def mean_se(xs):
    n = len(xs)
    m = sum(xs) / n
    sd = math.sqrt(sum((x - m) ** 2 for x in xs) / max(1, n - 1))
    return m, sd / math.sqrt(n)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("versions", nargs="+")
    ap.add_argument("--base")
    ap.add_argument("--handicap", type=int, default=0, help="candidates cannot shop before this round")
    ap.add_argument("--profiles", default="prof-", help="profile bot folder prefix under bots/_var")
    a = ap.parse_args()
    profiles = sorted((ROOT / "bots" / "_var").glob(a.profiles + "*"))
    if not profiles:
        sys.exit("no profile bots: run tools/profiles.py extract && tools/profiles.py build")
    for p in profiles:
        arena.build(p)
    maps = panel_maps()
    versions = list(dict.fromkeys(([a.base] if a.base else []) + a.versions))
    results = {v: play(v, profiles, maps, a.handicap) for v in versions}
    print(f"{len(profiles)} profiles x {len(maps)} maps x 2 sides" + (f", candidates handicapped to round {a.handicap}" if a.handicap else ""))
    print(f"  {'version':10s} {'games':>5s} {'win%':>5s} {'margin':>8s} {'deaths':>7s} {'gold':>7s} {'captured':>8s}")
    for v, rows in results.items():
        r = list(rows.values())
        m, se = mean_se([x["margin"] for x in r])
        print(f"  {v:10s} {len(r):5d} {100 * sum(x['won'] for x in r) / len(r):5.1f} {m:+8.1f} "
              f"{sum(x['deaths'] for x in r) / len(r):7.2f} {sum(x['gold'] for x in r) / len(r):7.0f} "
              f"{sum(x['captured'] for x in r) / len(r):8.0f}   (margin SE {se:.1f})")
    if a.base:
        base = results[a.base]
        for v, rows in results.items():
            if v == a.base:
                continue
            keys = sorted(set(rows) & set(base))
            for metric in ("margin", "deaths", "gold", "captured"):
                m, se = mean_se([rows[k][metric] - base[k][metric] for k in keys])
                print(f"  {v} - {a.base} {metric:9s} {m:+8.1f} ± {se:.1f}" + ("  **" if se and abs(m) >= 2 * se else ""))


if __name__ == "__main__":
    main()
