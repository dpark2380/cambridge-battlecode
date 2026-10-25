#!/usr/bin/env python3
"""One unattended development cycle: pull + analyse ranked games, tune a candidate, gate it, optionally submit.

    python3 tools/auto.py --base v8 --candidate v9-auto                      # dry run: no submission
    python3 tools/auto.py --base v8 --candidate v9-auto --submit             # submit if it passes the gate
    python3 tools/auto.py --base v8 --candidate v9-auto --skip-tune --submit # gate + submit hand-edited code

Steps (each logged to data/auto/<time>.log):
1. tools/ranked.py replays/daniel-<base> --replays losses: new ranked summaries, every new loss analysed into
   analysis/<match id>.txt and its replay deleted. Prints the per-map record.
2. Copy bots/daniel/<base> to bots/daniel/<candidate> unless the candidate already exists (so hand edits survive).
3. tools/tune.py --bot <candidate> --params <params> --apply (skipped with --skip-tune).
4. tools/arena.py <candidate> <base> --seeds <seeds> --min-winrate <gate>.
5. With --submit and a passing gate, `cambc submit` the candidate. Without --submit it only reports.

The candidate is never committed; review its diff and notes before promoting it to the next vN.
"""
import argparse
import datetime
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import arena  # noqa: E402

ROOT = arena.ROOT
# v8's main self-play constants (bots/daniel/docs/v8/summary.md, Tunables).
PARAMS = "recall_health,duo_recall_health,spawn_leave_health,extra_body_value,max_damage_share,gold_weight,monolith_hit_turns"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--base", default="v8", help="current submitted bot under bots/daniel/")
    parser.add_argument("--candidate", required=True, help="new bot folder under bots/daniel/")
    parser.add_argument("--params", default=PARAMS)
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--seeds", type=int, default=4, help="random-draft games per map and side in the gate")
    parser.add_argument("--gate", type=float, default=0.55, help="win rate vs base needed to submit")
    parser.add_argument("--since", default="", help="passed to ranked.py")
    parser.add_argument("--skip-tune", action="store_true")
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()

    log_path = ROOT / "data" / "auto" / f"{datetime.datetime.now():%Y%m%d-%H%M%S}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("w")

    def step(*cmd):
        print("$", *cmd, flush=True)
        log.write("$ " + " ".join(cmd) + "\n")
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        for line in proc.stdout:
            print(line, end="", flush=True)
            log.write(line)
        log.flush()
        return proc.wait()

    py = sys.executable
    step(py, "tools/ranked.py", f"replays/daniel-{args.base}", "--limit", "1000", "--replays", "losses",
         *(["--since", args.since] if args.since else []))

    base, candidate = ROOT / "bots/daniel" / args.base, ROOT / "bots/daniel" / args.candidate
    if not candidate.exists():
        shutil.copytree(base, candidate, ignore=shutil.ignore_patterns(".cambc", "build", "compile_commands.json"))
        print(f"copied {args.base} -> {args.candidate}")
    if not args.skip_tune and step(py, "tools/tune.py", "--bot", str(candidate), "--params", args.params,
                                   "--iterations", str(args.iterations), "--apply"):
        sys.exit("tune failed")

    passed = step(py, "tools/arena.py", str(candidate), str(base), "--seeds", str(args.seeds),
                  "--min-winrate", str(args.gate)) == 0
    print(f"gate {'passed' if passed else 'failed'} ({args.gate:.0%}); log {log_path.relative_to(ROOT)}")
    if passed and args.submit:
        sys.exit(step(arena.CAMBC, "submit", str(candidate), "--note", f"{args.candidate} (auto, gate {args.gate:.0%})"))
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
