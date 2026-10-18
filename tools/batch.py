#!/usr/bin/env python3
"""Play exact-size match sets, or a round robin of each member's newest bot.

    python3 tools/batch.py jame simon --games 20
    python3 tools/batch.py --round-robin --games 34
    python3 tools/batch.py --list

Uses only the standard library. Results, runner logs, statistics and replays are
saved under matches/. See docs/BatchTesting.md for probability assumptions.
"""
import argparse
import csv
import itertools
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Bot:
    name: str
    version: str
    path: str


def latest_bot(member):
    """Highest numbered version; prefer vN over a vN-suffix branch on a tie."""
    candidates = []
    for path in member.iterdir():
        if not (path / "src").is_dir():
            continue
        match = re.fullmatch(r"(?:main-)?v(\d+)(?:[-_](.+))?", path.name)
        if match:
            candidates.append(((int(match[1]), match[2] is None, path.name), path))
    if not candidates:
        raise ValueError(f"No numbered bot versions under {member}; specify a bot path explicitly.")
    path = max(candidates)[1].resolve()
    return Bot(member.name, path.name, str(path))


def members(root=ROOT):
    return [latest_bot(p) for p in sorted((root / "bots").iterdir())
            if p.is_dir() and not p.name.startswith((".", "_", "starter"))
            and any((c / "src").is_dir() for c in p.iterdir())]


def resolve_bot(value, root=ROOT):
    requested = Path(value).expanduser()
    path = next((p.resolve() for p in (requested, root / "bots" / value) if p.is_dir()), None)
    if path is None:
        # Preserve convenient bare version names, but never pick an ambiguous one.
        matches = sorted(p for p in (root / "bots").glob(f"*/{value}") if (p / "src").is_dir())
        if len(matches) != 1:
            raise ValueError(f"Unknown or ambiguous bot {value!r}; use a member name or explicit bot path.")
        path = matches[0].resolve()
    if not (path / "src").is_dir():
        return latest_bot(path)
    try:
        relative = path.relative_to((root / "bots").resolve())
    except ValueError:
        return Bot(path.name, path.name, str(path))
    name = relative.parts[0] if len(relative.parts) > 1 else path.name
    return Bot(name, path.name, str(path))


def contestants(values, root=ROOT, round_robin=False):
    if round_robin and values:
        raise ValueError("--round-robin selects every member's newest bot; omit explicit bot names.")
    bots = [resolve_bot(v, root) for v in values] if values else members(root)
    if len(bots) < 2:
        raise ValueError("At least two bots are needed.")
    if len({b.path for b in bots}) != len(bots):
        raise ValueError("The two selections resolve to the same bot; select different versions or members.")
    # Explicit comparisons of two versions of one member need distinct labels.
    return [Bot(f"{b.name}/{b.version}" if sum(x.name == b.name for x in bots) > 1 else b.name,
                b.version, b.path) for b in bots]


def clear_old_replays(parent, current):
    """Remove replay bundles from finished sibling batches, retaining their results.

    Never follow symlinks or trust manifest paths for deletion. Running batches,
    unrelated directories, and the new run are left alone.
    """
    removed = 0
    for directory in sorted(parent.iterdir()):
        if not directory.is_dir() or directory.is_symlink() or directory.resolve() == current.resolve():
            continue
        manifest = directory / "results.json"
        if not manifest.is_file() or manifest.is_symlink():
            continue
        if any((directory / name).is_symlink()
               for name in ("results.json.tmp", "report.md", "games.csv")):
            continue
        try:
            payload = json.loads(manifest.read_text())
        except (ValueError, OSError):
            continue
        if (not isinstance(payload, dict) or payload.get("status") != "finished"
                or not payload.get("bots") or not isinstance(payload.get("pairs"), list)):
            continue
        try:
            # Check the report schema before removing any files from this run.
            for pair in payload["pairs"]:
                pair["summary"] = summary(pair["games"])
            report(payload)
        except (KeyError, TypeError, ValueError, AttributeError):
            continue
        # Resolve every candidate before deleting any. A linked file/directory is
        # never a deletion target, including a link that points within the run.
        replays = [p for p in directory.rglob("*.repl26a") if p.is_file()]
        safe = []
        for replay in replays:
            relative = replay.relative_to(directory)
            if any((directory.joinpath(*relative.parts[:i])).is_symlink()
                   for i in range(1, len(relative.parts) + 1)):
                continue
            if replay.resolve().is_relative_to(directory.resolve()):
                safe.append(replay)
        if not safe:
            continue
        for replay in safe:
            replay.unlink()
        timestamp = datetime.now(timezone.utc).isoformat()
        for pair in payload["pairs"]:
            for game in pair["games"]:
                if game.get("replays"):
                    game["replays"] = []
                    game["replaysClearedAt"] = timestamp
        payload["replaysClearedAt"] = timestamp
        payload["replaysRemoved"] = payload.get("replaysRemoved", 0) + len(safe)
        save(payload, directory)
        removed += len(safe)
    return removed


def resolve_maps(values, root=ROOT):
    paths = []
    for value in values or sorted(p.stem for p in (root / "maps").glob("*.map26a")):
        candidate = Path(value).expanduser()
        if not candidate.is_file():
            candidate = root / "maps" / (value if value.endswith(".map26a") else value + ".map26a")
        if not candidate.is_file():
            raise ValueError(f"Map does not exist: {value}")
        candidate = str(candidate.resolve())
        if candidate not in paths:
            paths.append(candidate)
    if not paths:
        raise ValueError("No maps found.")
    return paths


def schedule(map_paths, games, seed):
    """Keep side swaps adjacent; cover every map before repeating a scenario."""
    rng = random.Random(seed)
    result = []
    while len(result) < games:
        cycle = list(map_paths)
        rng.shuffle(cycle)
        for map_path in cycle:
            # Randomize which participant starts a pair; retain both sides.
            first = bool(rng.getrandbits(1))
            for a_first in (first, not first):
                result.append((map_path, a_first))
                if len(result) == games:
                    return result
    return result


def probability_better(wins, losses):
    """P(p > .5), p ~ Beta(1+wins, 1+losses), evaluated without scipy.

    Equals P(Binomial(wins+losses+1, .5) <= wins). Sum the smaller
    tail in log space for numerical stability and symmetry.
    """
    if wins < 0 or losses < 0:
        raise ValueError("Win/loss counts must be nonnegative.")
    if wins == losses:
        return 0.5
    n = wins + losses + 1
    cutoff = min(wins, losses)
    tail = math.fsum(math.exp(math.lgamma(n + 1) - math.lgamma(k + 1)
                              - math.lgamma(n - k + 1) - n * math.log(2))
                     for k in range(cutoff + 1))
    return max(0.0, min(1.0, 1 - tail if wins > losses else tail))


def wilson(wins, total):
    if not total:
        return [0.0, 1.0]
    z = 1.959963984540054
    p = wins / total
    divisor = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / divisor
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / divisor
    return [max(0.0, centre - radius), min(1.0, centre + radius)]


def slug(value):
    """Portable, bounded filename component; never preserve path separators."""
    return re.sub(r"[^A-Za-z0-9_-]+", "-", value).strip("-_")[:40] or "unnamed"


def bot_tag(bot):
    label = bot.name if bot.name == bot.version or bot.name.endswith("/" + bot.version) else f"{bot.name}-{bot.version}"
    return slug(label)


def batch_name(bots, games, map_paths, started):
    """Describe the saved experiment before its timestamp."""
    tags = [bot_tag(b)[:28] for b in bots]
    matchup = "-vs-".join(tags) if len(tags) == 2 else "round-robin__" + "_".join(tags[:3])
    if len(tags) > 3:
        matchup += f"_plus-{len(tags) - 3}"
    count = f"{games}-games" + ("-per-pair" if len(tags) > 2 else "")
    maps = "_".join(slug(Path(p).stem)[:24] for p in map_paths) if len(map_paths) <= 2 else f"{len(map_paths)}-maps"
    stamp = datetime.fromisoformat(started).astimezone(timezone.utc).strftime("%Y-%m-%d_%H%M%S-UTC")
    return f"{matchup}__{count}__{maps}__{stamp}"


def unused_run_directory(directory):
    candidate, suffix = directory, 2
    while candidate.exists():
        candidate = directory.with_name(f"{directory.name}__{suffix}")
        suffix += 1
    return candidate


def batch_index(parent):
    """A readable entry point to saved sets, newest first."""
    runs = []
    for manifest in parent.glob("*/results.json"):
        payload = json.loads(manifest.read_text())
        runs.append((payload["started"], manifest.parent, payload))
    lines = ["# Saved batch games", "", "Open a report for results and links to each replay. Times are UTC.", "",
             "| Started | Participants | Games collected / scheduled | Results (wins) | Status | Report |",
             "| --- | --- | --- | --- | --- | --- |"]
    for started, directory, payload in sorted(runs, reverse=True, key=lambda r: (r[0], r[1].name)):
        bots = ", ".join(bot_tag(Bot(**b)) for b in payload["bots"])
        collected = sum(len(p["games"]) for p in payload["pairs"])
        scheduled = sum(p["requested"] for p in payload["pairs"])
        results = "; ".join(f"{p['a']} {p['summary']['winsA']}–{p['summary']['winsB']} {p['b']}"
                            for p in payload["pairs"])
        lines.append(f"| {started[:19].replace('T', ' ')} | {bots} | {collected}/{scheduled} | {results}"
                     f" | {payload.get('status', 'unknown')} | [Open report](<{directory.name}/report.md>) |")
    (parent / "index.md").write_text("\n".join(lines) + "\n")


def game_directory(output, pair_index, game_index, a, b, map_path, a_first):
    first, second = (a, b) if a_first else (b, a)
    return (output / f"pair-{pair_index + 1:02d}__{bot_tag(a)}-vs-{bot_tag(b)}"
            / f"game-{game_index:04d}__{slug(Path(map_path).stem)}__A-{bot_tag(first)}__B-{bot_tag(second)}")


def rename_replays(a, b, record, apply=True):
    """Rename a completed game's bundles, refusing to overwrite existing files."""
    first, second = (a, b) if record["aFirst"] else (b, a)
    score_first, score_second = ((record["gemsA"], record["gemsB"]) if record["aFirst"]
                                else (record["gemsB"], record["gemsA"]))
    winner = a if record["aWon"] else b
    stem = (f"game-{record['game']:04d}__{slug(record['map'])}"
            f"__A-{bot_tag(first)}-{score_first}__B-{bot_tag(second)}-{score_second}"
            f"__winner-{bot_tag(winner)}__r{record['rounds']}")
    paths = [Path(p) for p in record.get("replays", [])]
    moves = []
    for index, source in enumerate(paths, 1):
        extra = f"__part-{index}" if len(paths) > 1 else ""
        destination = source.with_name(stem + extra + ".repl26a")
        if not source.is_file():
            raise FileNotFoundError(f"Replay is missing: {source}")
        if destination != source and destination.exists():
            raise FileExistsError(f"Refusing to overwrite replay: {destination}")
        moves.append((source, destination))
    if not apply:
        return
    for source, destination in moves:
        if source != destination:
            source.rename(destination)
    record["replays"] = [str(destination) for _, destination in moves]


def relabel_saved_run(directory):
    """Upgrade existing batch filenames and manifests without rerunning games."""
    directory = directory.expanduser().resolve()
    payload = json.loads((directory / "results.json").read_text())
    bots = {b["name"]: Bot(**b) for b in payload["bots"]}
    # Validate the entire manifest before touching anything outside its run.
    for pair in payload["pairs"]:
        for game in pair["games"]:
            for filename in game.get("replays", []):
                if not Path(filename).resolve().is_relative_to(directory):
                    raise ValueError(f"Replay is outside the selected run: {filename}")
            if game["status"] == "completed":
                rename_replays(bots[pair["a"]], bots[pair["b"]], game, apply=False)
    renamed = 0
    for pair in payload["pairs"]:
        for game in pair["games"]:
            if game["status"] != "completed":
                continue
            before = list(game.get("replays", []))
            rename_replays(bots[pair["a"]], bots[pair["b"]], game)
            renamed += sum(a != b for a, b in zip(before, game["replays"]))
    save(payload, directory)
    return renamed


def rename_saved_batch(directory):
    """Give an old run and its game folders descriptive names; preserve artifacts."""
    directory = directory.expanduser().resolve()
    payload = json.loads((directory / "results.json").read_text())
    if payload.get("status") == "running":
        raise ValueError("Cannot rename a batch while it is running.")
    bots = {b["name"]: Bot(**b) for b in payload["bots"]}
    destination = directory.with_name(batch_name(list(bots.values()), payload["gamesPerPair"],
                                                payload["maps"], payload["started"]))
    if destination != directory and destination.exists():
        raise FileExistsError(f"Refusing to overwrite batch: {destination}")
    moves, seen, sources = [], set(), set()
    for pair_index, pair in enumerate(payload["pairs"]):
        for game in pair["games"]:
            source = Path(game["directory"]).resolve()
            if not source.is_relative_to(directory) or not source.is_dir():
                raise ValueError(f"Missing game directory or outside the selected batch: {source}")
            target = game_directory(directory, pair_index, game["game"], bots[pair["a"]], bots[pair["b"]],
                                    game["mapPath"], game["aFirst"])
            if source in sources or target in seen or (target != source and target.exists()):
                raise FileExistsError(f"Refusing to overwrite game directory: {target}")
            seen.add(target)
            sources.add(source)
            moves.append((source, target, game))
    # Replay validation happens before any folder moves.
    relabel_saved_run(directory)
    payload = json.loads((directory / "results.json").read_text())
    games = {g["directory"]: g for p in payload["pairs"] for g in p["games"]}
    # Rebind records after replay renaming refreshed their paths.
    for source, target, original in moves:
        game = games[original["directory"]]
        if source != target:
            target.parent.mkdir(parents=True, exist_ok=True)
            source.rename(target)
            if source.parent != directory and not any(source.parent.iterdir()):
                source.parent.rmdir()
        def relocate(value):
            path = Path(value)
            if path.is_absolute() and path.is_relative_to(source):
                return str(destination / target.relative_to(directory) / path.relative_to(source))
            if path.is_absolute() and path.is_relative_to(directory):
                return str(destination / path.relative_to(directory))
            return value
        game["directory"] = relocate(game["directory"])
        game["replays"] = [relocate(p) for p in game.get("replays", [])]
        game["command"] = [relocate(p) for p in game.get("command", [])]
    if destination != directory:
        directory.rename(destination)
    save(payload, destination)
    batch_index(destination.parent)
    return destination


def play(cli, bot_a, bot_b, map_path, a_first, directory, timeout, game_number=1):
    stats_path = directory / "statistics.json"
    first, second = (bot_a, bot_b) if a_first else (bot_b, bot_a)
    command = [cli, "run", first.path, second.path, "--map", map_path,
               "-o", str(directory), "--statistics", str(stats_path)]
    record = {"map": Path(map_path).stem, "mapPath": map_path, "aFirst": a_first,
              "game": game_number, "status": "failed", "directory": str(directory), "command": command}
    try:
        directory.mkdir(parents=True)
        process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=timeout)
        (directory / "runner.log").write_text(process.stdout + process.stderr)
        if process.returncode:
            raise ValueError(f"Runner exited with code {process.returncode}; see runner.log")
        data = json.loads(stats_path.read_text())
        if data["outcome"] not in ("teamA", "teamB"):
            raise ValueError(f"Match has no recognized completed outcome: {data['outcome']!r}")
        index = 0 if a_first else 1
        # Index by team ID rather than assuming exported array order.
        teams = {int(t["team"]): t for t in data["teams"]}
        gems_a, gems_b = (int(teams[t]["submittedGems"]) for t in (index, 1 - index))
        faults_a, faults_b = (int(data["botFaults"][t]) for t in (index, 1 - index))
        record.update(aWon=data["outcome"] == ("teamA" if a_first else "teamB"),
                      gemsA=gems_a, gemsB=gems_b, margin=gems_a - gems_b, rounds=int(data["round"]),
                      faultsA=faults_a, faultsB=faults_b, engineVersion=data.get("engineVersion"),
                      replays=[str(p) for p in sorted(directory.glob("*.repl26a"))])
        rename_replays(bot_a, bot_b, record)
        record["status"] = "completed"
    except subprocess.TimeoutExpired as error:
        def decode(value):
            return value.decode(errors="replace") if isinstance(value, bytes) else value or ""
        (directory / "runner.log").write_text(decode(error.stdout) + decode(error.stderr))
        record["error"] = f"Timed out after {timeout:g} seconds"
    except (OSError, ValueError, KeyError, TypeError, IndexError) as error:
        record["error"] = str(error)
    return record


def summary(records):
    completed = [r for r in records if r["status"] == "completed"]
    # Scheduling indices, not completion order, determine which repeat counts.
    evidence = {}
    for record in sorted(completed, key=lambda r: r["game"]):
        evidence.setdefault((record["mapPath"], record["aFirst"]), record)
    unique = list(evidence.values())
    wins = sum(r["aWon"] for r in completed)
    unique_wins = sum(r["aWon"] for r in unique)
    return {"completed": len(completed), "failed": len(records) - len(completed),
            "winsA": wins, "winsB": len(completed) - wins,
            "winRateA": wins / len(completed) if completed else None,
            "meanGemMarginA": sum(r["margin"] for r in completed) / len(completed) if completed else None,
            "faultsA": sum(r["faultsA"] for r in completed), "faultsB": sum(r["faultsB"] for r in completed),
            "uniqueScenarios": len(unique), "uniqueWinsA": unique_wins,
            "repeatedScenariosExcluded": len(completed) - len(unique),
            "uniqueWinRateWilson95": wilson(unique_wins, len(unique)),
            "probabilityABetter": probability_better(unique_wins, len(unique) - unique_wins)}


def percentage(value):
    return "n/a" if value is None else f"{100 * value:.1f}%"


def probability_percentage(value):
    # Do not round strong but finite evidence into apparent certainty.
    if value > 0.999:
        return ">99.9%"
    if value < 0.001:
        return "<0.1%"
    return percentage(value)


def standings(payload):
    rows = {b["name"]: {"name": b["name"], "games": 0, "wins": 0, "losses": 0, "faults": 0}
            for b in payload["bots"]}
    for pair in payload["pairs"]:
        s = pair["summary"]
        for name, wins, losses, faults in ((pair["a"], s["winsA"], s["winsB"], s["faultsA"]),
                                           (pair["b"], s["winsB"], s["winsA"], s["faultsB"])):
            row = rows[name]
            row["games"] += wins + losses
            row["wins"] += wins
            row["losses"] += losses
            row["faults"] += faults
    for row in rows.values():
        row["winRate"] = row["wins"] / row["games"] if row["games"] else None
    return sorted(rows.values(), key=lambda r: (-(r["winRate"] if r["winRate"] is not None else -1), r["name"]))


def report(payload):
    collected = sum(len(p["games"]) for p in payload["pairs"])
    scheduled = sum(p["requested"] for p in payload["pairs"])
    lines = ["# Batch match results", "", f"Started: {payload['started']}",
             f"Status: {payload.get('status', 'running')}; results collected: {collected}/{scheduled}", "",
             "## Participants", "", "| Member | Version | Source |", "| --- | --- | --- |"]
    if payload.get("replaysClearedAt"):
        lines[4:4] = [f"Old replay bundles cleared: {payload['replaysClearedAt']}. Results and logs retained.", ""]
    for bot in payload["bots"]:
        lines.append(f"| {bot['name']} | {bot['version']} | `{bot['path']}` |")
    lines += ["", "## Standings (observed game win rate)", "",
              "| Member | Played | Wins | Losses | Win rate | Bot faults |", "| --- | --- | --- | --- | --- | --- |"]
    for row in standings(payload):
        lines.append(f"| {row['name']} | {row['games']} | {row['wins']} | {row['losses']}"
                     f" | {percentage(row['winRate'])} | {row['faults']} |")
    lines += ["", "## Match sets", "",
              "| Matchup | Wins | A win rate | Mean A gem margin | Failed | P(A win rate > 50%) | Unique evidence |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for pair in payload["pairs"]:
        s = pair["summary"]
        margin = "n/a" if s["meanGemMarginA"] is None else f"{s['meanGemMarginA']:+.1f}"
        probability = probability_percentage(s["probabilityABetter"]) if s["uniqueScenarios"] else "n/a (no evidence)"
        lines.append(f"| {pair['a']} vs {pair['b']} | {s['winsA']}–{s['winsB']} | {percentage(s['winRateA'])}"
                     f" | {margin} | {s['failed']} | {probability} | {s['uniqueWinsA']}/{s['uniqueScenarios']} |")
    lines += ["", "## Interpretation", "",
              "The probability uses a uniform Beta(1,1) prior and completed distinct map/side scenarios."
              " Identical repeats do not add evidence. It estimates whether the first named bot's win rate"
              " exceeds 50% under a simple Bernoulli model for this test setup; it is not a next-game win"
              " probability or proof of superiority on unseen maps. Different scenarios may still be correlated.",
              "", "Engine tiebreak outcomes count as wins even if gem scores are equal. Failed runs are"
              " excluded, reported separately, and make the command exit unsuccessfully. Bot faults in a"
              " completed game remain part of its performance result.",
              "", "Only normal default fuel was used. The schedule seed randomizes map order and starting"
              " sides; it is not a game-engine or draft seed.", "", "## Per-map and side details", ""]
    for pair in payload["pairs"]:
        lines += [f"### {pair['a']} vs {pair['b']}", "",
                  "| Map | First bot's side | Wins | Mean gem margin | Failed |", "| --- | --- | --- | --- | --- |"]
        groups = sorted({(r["map"], r["aFirst"]) for r in pair["games"]})
        for map_name, a_first in groups:
            rs = [r for r in pair["games"] if r["map"] == map_name and r["aFirst"] == a_first]
            s = summary(rs)
            margin = "n/a" if s["meanGemMarginA"] is None else f"{s['meanGemMarginA']:+.1f}"
            lines.append(f"| {map_name} | {'A' if a_first else 'B'} | {s['winsA']}–{s['winsB']} | {margin} | {s['failed']} |")
        s = pair["summary"]
        low, high = s["uniqueWinRateWilson95"]
        lines += ["", f"Unique-scenario win-rate Wilson 95% interval: {percentage(low)}–{percentage(high)}."
                  f" Repeated completed scenarios excluded from inference: {s['repeatedScenariosExcluded']}."
                  f" Bot faults: {pair['a']} {s['faultsA']}, {pair['b']} {s['faultsB']}.", ""]
    lines += ["## Replay index", "", "| Game | Map | Team A | Team B | Winner | Round | Replay |",
              "| --- | --- | --- | --- | --- | --- | --- |"]
    for pair in payload["pairs"]:
        for game in pair["games"]:
            if game["status"] != "completed":
                continue
            a_name, b_name = pair["a"], pair["b"]
            first, second = ((f"{a_name} {game['gemsA']}", f"{b_name} {game['gemsB']}") if game["aFirst"]
                             else (f"{b_name} {game['gemsB']}", f"{a_name} {game['gemsA']}"))
            links = " ".join(f"[Replay {i}](<{path}>)" for i, path in enumerate(game.get("replays", []), 1))
            if game.get("replaysClearedAt"):
                links = "Cleared by a newer batch"
            lines.append(f"| {game['game']} | {game['map']} | {first} | {second}"
                         f" | {a_name if game['aWon'] else b_name} | {game['rounds']} | {links} |")
    return "\n".join(lines) + "\n"


def save(payload, directory):
    for pair in payload["pairs"]:
        pair["games"].sort(key=lambda r: r["game"])
        pair["summary"] = summary(pair["games"])
    payload["standings"] = standings(payload)
    temporary = directory / "results.json.tmp"
    temporary.write_text(json.dumps(payload, indent=2) + "\n")
    temporary.replace(directory / "results.json")
    (directory / "report.md").write_text(report(payload))
    fields = ["a", "b", "game", "map", "aFirst", "status", "aWon", "gemsA", "gemsB", "margin",
              "rounds", "faultsA", "faultsB", "error", "directory", "replays", "replaysClearedAt"]
    with (directory / "games.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for pair in payload["pairs"]:
            for game in pair["games"]:
                writer.writerow({**game, "a": pair["a"], "b": pair["b"], "replays": ";".join(game.get("replays", []))})


def positive_int(value):
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("bots", nargs="*", help="two member names or bot paths; omit for newest-member round robin")
    parser.add_argument("--round-robin", action="store_true",
                        help="compare every member's newest bot against every other member; excludes starters")
    parser.add_argument("--keep-old-replays", action="store_true",
                        help="keep finished older batches' replay bundles (default: clear siblings after builds succeed)")
    parser.add_argument("--games", "-n", type=positive_int, help="games per pair; default: twice the number of selected maps")
    parser.add_argument("--maps", nargs="+", help="map names or .map26a paths; default: all local maps")
    parser.add_argument("--jobs", "-j", type=positive_int, default=min(4, os.cpu_count() or 1))
    parser.add_argument("--timeout", type=positive_int, default=120, help="seconds per game, default: 120")
    parser.add_argument("--seed", type=int, default=0, help="schedule shuffle seed, not an engine seed")
    parser.add_argument("--out", "-o", type=Path, help="new or empty output directory")
    parser.add_argument("--cambc", help="CLI executable override")
    parser.add_argument("--list", action="store_true", help="list each member's newest bot without running games")
    parser.add_argument("--rename-replays", type=Path, metavar="RUN_DIR",
                        help="rename an existing batch's replay files and refresh its reports, without playing games")
    parser.add_argument("--rename-batch", type=Path, metavar="RUN_DIR",
                        help="rename an existing batch folder, game folders and replays; refresh saved links")
    args = parser.parse_args(argv)
    try:
        if args.rename_batch:
            output = rename_saved_batch(args.rename_batch)
            print(f"Batch folders and saved links updated: {output}\nBrowse saved sets: {output.parent / 'index.md'}")
            return 0
        if args.rename_replays:
            renamed = relabel_saved_run(args.rename_replays)
            print(f"Renamed {renamed} replay files; JSON, CSV and replay index refreshed in {args.rename_replays}.")
            return 0
        if args.list:
            for bot in members():
                print(f"{bot.name:12s} {bot.version:12s} {bot.path}")
            return 0
        if len(args.bots) not in (0, 2):
            raise ValueError("Supply exactly two bots, or no bots for a newest-member round robin.")
        bots = contestants(args.bots, round_robin=args.round_robin)
        map_paths = resolve_maps(args.maps)
        games = args.games or 2 * len(map_paths)
        local_cli = next((str(p) for p in (ROOT / ".venv/bin/cambc", ROOT / ".venv/Scripts/cambc.exe") if p.is_file()), None)
        cli = str(Path(args.cambc).expanduser()) if args.cambc else local_cli or shutil.which("cambc")
        if not cli:
            raise ValueError("cambc was not found; install it or supply --cambc /path/to/cambc.")
        started = datetime.now(timezone.utc)
        output = (args.out.expanduser() if args.out else unused_run_directory(ROOT / "matches" /
                  batch_name(bots, games, map_paths, started.isoformat()))).resolve()
        if output.exists() and (not output.is_dir() or any(output.iterdir())):
            raise ValueError(f"Output must be a new or empty directory: {output}")
        output.mkdir(parents=True, exist_ok=True)
        print("Selected bots:", flush=True)
        for bot in bots:
            print(f"  {bot.name}: {bot.version} ({bot.path})", flush=True)
        for index, bot in enumerate(bots):
            print(f"Building {bot.name}...", flush=True)
            build = subprocess.run([cli, "build", bot.path], cwd=ROOT, capture_output=True, text=True, timeout=args.timeout)
            (output / f"build-{index}.log").write_text(build.stdout + build.stderr)
            if build.returncode:
                raise ValueError(f"Build failed for {bot.name}; see {output / f'build-{index}.log'}")
        if not args.keep_old_replays:
            removed = clear_old_replays(output.parent, output)
            print(f"Cleared {removed} old batch replay bundles; saved results and logs retained.", flush=True)
    except (ValueError, OSError, subprocess.TimeoutExpired) as error:
        parser.error(str(error))

    pairs = list(itertools.combinations(bots, 2))
    plan = schedule(map_paths, games, args.seed)
    payload = {"started": started.isoformat(), "status": "running", "gamesPerPair": games, "scheduleSeed": args.seed,
               "maps": map_paths, "bots": [asdict(b) for b in bots], "pairs": []}
    for a, b in pairs:
        payload["pairs"].append({"a": a.name, "b": b.name, "requested": games, "games": []})
    save(payload, output)
    batch_index(output.parent)
    total = games * len(pairs)
    print(f"Running {total} games ({games} per pair), {args.jobs} workers. Results: {output}", flush=True)
    if games > 2 * len(map_paths):
        print("Repeated map/side scenarios will not increase probability evidence.", flush=True)
    if games % 2:
        print("Odd game count: each set has one extra game on one side.", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {}
        for pair_index, (a, b) in enumerate(pairs):
            for game_index, (map_path, a_first) in enumerate(plan, 1):
                directory = game_directory(output, pair_index, game_index, a, b, map_path, a_first)
                future = pool.submit(play, cli, a, b, map_path, a_first, directory, args.timeout, game_index)
                futures[future] = (pair_index, game_index)
        for future in as_completed(futures):
            pair_index, game_index = futures[future]
            result = future.result()
            result["game"] = game_index
            pair = payload["pairs"][pair_index]
            pair["games"].append(result)
            done += 1
            if result["status"] == "completed":
                winner = pair["a"] if result["aWon"] else pair["b"]
                detail = (f"{pair['a']} {result['gemsA']} - {pair['b']} {result['gemsB']}"
                          f" | winner: {winner} | round {result['rounds']}")
            else:
                detail = f"FAILED: {result['error']}"
            print(f"[{done}/{total}] {pair['a']} vs {pair['b']} | {result['map']} | "
                  f"{pair['a']} as {'A' if result['aFirst'] else 'B'} | {detail}", flush=True)
            save(payload, output)
    payload["status"] = "finished"
    payload["finished"] = datetime.now(timezone.utc).isoformat()
    save(payload, output)
    batch_index(output.parent)
    print("\nSet results:")
    for pair in payload["pairs"]:
        s = pair["summary"]
        probability = probability_percentage(s["probabilityABetter"]) if s["uniqueScenarios"] else "n/a"
        print(f"  {pair['a']} vs {pair['b']}: {s['winsA']}–{s['winsB']} "
              f"({percentage(s['winRateA'])}), P({pair['a']} win rate > 50%)={probability}; "
              f"{s['uniqueScenarios']} unique scenarios; {s['failed']} failed")
    print("\nStandings (observed game win rate):")
    previous_rate, rank = object(), 0
    for position, row in enumerate(payload["standings"], 1):
        if row["winRate"] != previous_rate:
            rank = position
        previous_rate = row["winRate"]
        print(f"  {rank}. {row['name']:16s} {row['wins']}–{row['losses']} "
              f"({percentage(row['winRate'])}); faults {row['faults']}")
    print("Probability: Beta(1,1) prior, distinct completed map/side setups; conditional model, not proof on unseen maps.")
    print(f"Full report: {output / 'report.md'}\nMachine results: {output / 'results.json'}\nPer-game CSV: {output / 'games.csv'}")
    return 1 if any(p["summary"]["failed"] for p in payload["pairs"]) else 0


if __name__ == "__main__":
    sys.exit(main())
