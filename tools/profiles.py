#!/usr/bin/env python3
"""Profile bots: sparring opponents built from the scrim-panel opponents' own games (process review #9, stdlib only).

    python3 tools/profiles.py extract                 # data/profiles/<team>.json from data/scrims/*p2/summaries
    python3 tools/profiles.py build [--base v51]      # bots/_var/prof-<team>/ = base bot + that team's profile
    python3 tools/profiles.py show                    # one line per profile

A profile copies what the summaries record about a team, not how it moves or fights:
  picks   the team's most common ordered roster per team size (Cassi and Issac are one pick)
  builds  per champion: the emblem families it completes, in the order it starts them, then the family it buys most
          (the soak) and the health share of that soak; families under 3 shards a game are dropped
  bag     the median tribute size (gemSubmission), used as the bot's banking threshold
The bot is the base bot (our movement, targeting and fights) with draft, shop order and banking replaced, so a local
gate against the profiles asks: does a change still work against these drafts, these builds and this banking?
Validate a profile set with a calibration check before trusting it (process review §1.5 #3).
"""
import argparse
import collections
import glob
import gzip
import json
import re
import shutil
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "profiles"
DRAFT = ["ryth", "vesper_vale", "vendetta", "cassi_and_issac", "stellar", "prism", "marcella", "willow", "ren", "varg",
         "tavi", "heart_of_ruin"]


def champ_key(name):
    """Summary name -> champion_type name ('Vesper Vale' -> vesper_vale)."""
    return name.lower().replace(" ", "_")


def draft_key(name):
    k = champ_key(name)
    return "cassi_and_issac" if k in ("cassi", "issac", "cassi_&_issac") else k


def slug(team):
    return re.sub(r"[^a-z0-9]+", "-", team.lower()).strip("-")


def scout_games(engine):
    """Top-team games from tools/scout.py: data/scout/features.jsonl rows name the scouted team and its side."""
    games = collections.defaultdict(list)
    seen = set()
    for line in (ROOT / "data" / "scout" / "features.jsonl").read_text().splitlines():
        r = json.loads(line)
        path = ROOT / "data" / "scout" / "summaries" / f"{r['match']}.json.gz"
        if not r.get("team") or (r["match"], r["team"]) in seen or not path.exists():
            continue
        seen.add((r["match"], r["team"]))
        if engine and json.load(gzip.open(path, "rt"))["match"].get("engineVersion") != engine:
            continue
        games[r["team"]].append((path, r["side"]))
    return games


def extract(pattern="*p2*", scout_engine=None):
    games = scout_games(scout_engine) if scout_engine else collections.defaultdict(list)  # team -> [(summary, their side)]
    for vdir in ([] if scout_engine else sorted(glob.glob(str(ROOT / "data" / "scrims" / pattern)))):
        feats = Path(vdir) / "features.jsonl"
        if not feats.exists():
            continue
        for line in feats.read_text().splitlines():
            r = json.loads(line)
            path = Path(vdir) / "summaries" / f"{r['match']}.json.gz"
            if path.exists():
                games[r["team"]].append((path, "teamB" if r["side"] == "teamA" else "teamA"))
    OUT.mkdir(parents=True, exist_ok=True)
    for team, items in sorted(games.items()):
        rosters = collections.defaultdict(collections.Counter)
        first = collections.defaultdict(lambda: collections.defaultdict(list))  # champ -> family -> [first-buy rounds]
        qty = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))  # champ -> family -> stat -> n
        appearances = collections.Counter()
        bags = []
        for path, side in items:
            s = json.load(gzip.open(path, "rt"))
            picks = []
            for d in s["roster"]["draft"]:
                if d["team"] == side and draft_key(d["champion"]) not in picks:
                    picks.append(draft_key(d["champion"]))
            rosters[len(picks)][tuple(picks)] += 1
            seen = collections.defaultdict(dict)
            for e in s["events"]:
                owner = e["owner"]
                if owner.get("team") != side:
                    continue
                c = champ_key(owner.get("name", ""))
                if e["kind"] == "buyItem":
                    for x in e["entries"]:
                        m = re.match(r"(\w+) Shard of (\w+)", x["target"]["name"])
                        if not m:
                            continue
                        fam, stat = m[1].lower(), m[2].lower()
                        qty[c][fam][stat] += int(x["value"])
                        seen[c].setdefault(fam, x["timestamp"]["round"])
                elif e["kind"] == "gemSubmission":
                    bags += [int(x["value"]) for x in e["entries"]]
            for c, fams in seen.items():
                appearances[c] += 1
                for fam, rnd in fams.items():
                    first[c][fam].append(rnd)
        builds = {}
        for c, fams in qty.items():
            n = appearances[c] or 1
            total = {f: sum(st.values()) for f, st in fams.items()}
            soak = max(total, key=total.get)
            emblems = [f for f in sorted(first[c], key=lambda f: statistics.median(first[c][f]))
                       if f != soak and total[f] / n >= 3]
            def main_stat(f):
                st = fams[f]
                non_health = {k: v for k, v in st.items() if k != "health"}
                return max(non_health, key=non_health.get) if non_health else "health"
            soak_stat = main_stat(soak)
            builds[c] = {"emblems": [f"{f}_shard_of_{main_stat(f) if f != 'durability' else 'health'}" for f in emblems],
                         "soak": f"{soak}_shard_of_{soak_stat}",
                         "health_share": round(fams[soak].get("health", 0) / max(1, total[soak]), 2),
                         "games": appearances[c]}
        prof = {"team": team, "games": len(items),
                "picks": {str(k): list(v.most_common(1)[0][0]) for k, v in rosters.items()},
                "builds": builds,
                "bag": int(statistics.median(bags)) if bags else 25}
        (OUT / f"{slug(team)}.json").write_text(json.dumps(prof, indent=1))
        print(f"{team}: {len(items)} games -> {OUT / (slug(team) + '.json')}")


def header(prof):
    """C++ profile.h for the bot."""
    lines = ["#pragma once", "// Generated by tools/profiles.py from " + prof["team"] + "'s panel games; do not edit.",
             "#include <cambc.h>", "#include <optional>", "#include <vector>", "",
             "inline std::vector<cambc::champion_draft> profile_picks(std::size_t size) {",
             "    using cambc::champion_draft;", "    switch (size) {"]
    for size, picks in sorted(prof["picks"].items()):
        lines.append(f"    case {size}: return {{" + ", ".join(f"champion_draft::{p}" for p in picks) + "};")
    lines += ["    default: return {};", "    }", "}", "",
              "struct profile_build { std::vector<cambc::item_type> order; float health_share; cambc::item_type health; };",
              "inline std::optional<profile_build> profile_build_for(cambc::champion_type c) {",
              "    using cambc::item_type;", "    using cambc::champion_type;"]
    for c, b in sorted(prof["builds"].items()):
        order = ", ".join(f"item_type::{i}" for i in b["emblems"] + [b["soak"]])
        health = b["soak"].split("_shard_of_")[0] + "_shard_of_health"
        lines.append(f"    if (c == champion_type::{c}) return profile_build{{{{{order}}}, {b['health_share']}f, item_type::{health}}};")
    lines += ["    return std::nullopt;", "}", "", f"constexpr int profile_bag = {max(10, min(40, prof['bag']))};", ""]
    return "\n".join(lines)


def build(base, prefix="prof-", only=None):
    src = ROOT / "bots" / "daniel" / base
    for path in sorted(OUT.glob("*.json")):
        if only and path.stem not in only:
            continue
        prof = json.loads(path.read_text())
        dst = ROOT / "bots" / "_var" / f"{prefix}{path.stem}"
        shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(src, dst, ignore=shutil.ignore_patterns(".cambc"))
        (dst / "src" / "profile.h").write_text(header(prof))
        d = (dst / "src" / "draft.cpp").read_text()
        old = "    const auto team = seed > 0 ? random_team(seed, ours, size)\n        : can_score ? project_team(*profile, ours) : fallback_team(ours, size);"
        assert d.count(old) == 1, "draft hook"
        new = old.replace("const auto team", "auto team") + """
    // Profile bot: the opponent's own roster for this team size, then our pick for any gap.
    if (const auto wanted = profile_picks(size); !wanted.empty()) {
        std::vector<champion_draft> mine(ours.begin(), ours.end());
        for (const auto p : wanted)
            if (mine.size() < size && std::find(mine.begin(), mine.end(), p) == mine.end()) mine.push_back(p);
        for (const auto p : team)
            if (mine.size() < size && std::find(mine.begin(), mine.end(), p) == mine.end()) mine.push_back(p);
        team = mine;
    }"""
        d = d.replace(old, new)
        d = d.replace('#include "plan.h"', '#include "plan.h"\n#include "profile.h"\n#include <algorithm>', 1)
        assert '#include "profile.h"' in d, "draft include"
        (dst / "src" / "draft.cpp").write_text(d)
        b = (dst / "src" / "bot.cpp").read_text()
        old = "    const auto order = build_order(build_stat[static_cast<int>(me.champion_name())]);"
        assert b.count(old) == 1, "shop hook"
        b = b.replace(old, """    const auto prof = profile_build_for(me.champion_name());  // profile bot: the opponent's build
    const auto order = prof ? prof->order : build_order(build_stat[static_cast<int>(me.champion_name())]);""")
        old = "                const float health_share = me.champion_name() == cambc::champion_type::heart_of_ruin ? 0.65f : power_health_share;"
        assert b.count(old) == 1, "health hook"
        b = b.replace(old, "                const float health_share = prof ? prof->health_share : me.champion_name() == cambc::champion_type::heart_of_ruin ? 0.65f : power_health_share;")
        old = "            const auto health = cambc::item_type::bruiser_shard_of_health;"
        assert b.count(old) == 1, "health item hook"
        b = b.replace(old, "            const auto health = prof ? prof->health : cambc::item_type::bruiser_shard_of_health;")
        old = "        if (last && power_health_share > 0 && shard != cambc::item_type::bruiser_shard_of_health) {"
        assert b.count(old) == 1, "split hook"
        b = b.replace(old, "        if (last && power_health_share > 0 && shard != (prof ? prof->health : cambc::item_type::bruiser_shard_of_health)) {")
        for name in ("tribute_gems", "threat_tribute_gems"):
            b, n = re.subn(rf"constexpr int {name} = \d+;", f"constexpr int {name} = profile_bag;", b)
            assert n == 1, name
        b = b.replace('#include "bot.h"', '#include "bot.h"\n#include "profile.h"', 1)
        assert '#include "profile.h"' in b, "bot include"
        (dst / "src" / "bot.cpp").write_text(b)
        print(f"{prof['team']}: {dst.relative_to(ROOT)}")


def show():
    for path in sorted(OUT.glob("*.json")):
        p = json.loads(path.read_text())
        builds = "; ".join(f"{c}: {'/'.join(i.split('_shard')[0] for i in b['emblems'])} then {b['soak'].replace('_shard_of_', ':')} ({b['health_share']:.0%} health)"
                           for c, b in sorted(p["builds"].items()))
        print(f"{p['team']} ({p['games']} games) picks {p['picks']} bag {p['bag']}\n   {builds}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("command", choices=["extract", "build", "show"])
    ap.add_argument("--base", default="v51")
    ap.add_argument("--prefix", default="prof-", help="build: folder prefix under bots/_var (a candidate, not a sparring bot)")
    ap.add_argument("--only", nargs="*", help="build: these profile slugs only")
    ap.add_argument("--scrims", default="*p2*", help="extract: data/scrims folders to read (glob)")
    ap.add_argument("--out", help="extract/build/show: profile folder (default data/profiles)")
    ap.add_argument("--scout", metavar="ENGINE", help="extract: from the scouted top teams' games on this engine version (e.g. 3.0.0)")
    a = ap.parse_args()
    global OUT
    if a.out:
        OUT = ROOT / a.out
    {"extract": lambda: extract(a.scrims, a.scout), "build": lambda: build(a.base, a.prefix, a.only), "show": show}[a.command]()


if __name__ == "__main__":
    main()
