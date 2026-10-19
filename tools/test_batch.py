"""Contract tests for selection, scheduling, inference, and runner failures.

Run: python3 -m unittest discover -s tools -p test_batch.py
"""
import json
import io
import math
import subprocess
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

import batch


def result(number, won=True, first=True, map_path="map", **changes):
    return {"game": number, "status": "completed", "map": map_path, "mapPath": map_path,
            "aFirst": first, "aWon": won, "margin": 12 if won else -12,
            "faultsA": 0, "faultsB": 0, **changes}


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()

    def bot(self, name):
        directory = self.root / "bots" / name
        (directory / "src").mkdir(parents=True)
        return directory

    def test_latest_is_numeric_and_plain_release_beats_same_number_branch(self):
        self.bot("alice/v9")
        expected = self.bot("alice/v10")
        self.bot("alice/v10-dp")
        self.bot("alice/main-v2")
        self.bot("alice/main-cpp")
        selected = batch.latest_bot(self.root / "bots/alice")
        self.assertEqual((selected.name, selected.version, selected.path), ("alice", "v10", str(expected)))

    def test_default_discovers_members_and_ignores_starters_and_scratch(self):
        self.bot("alice/v1")
        self.bot("bob/v2")
        self.bot("starter-cpp")
        self.bot("starter-example/v1")
        self.bot("_tuning/v99")
        self.assertEqual([b.name for b in batch.contestants([], self.root)], ["alice", "bob"])

    def test_explicit_round_robin_selects_every_latest_member_and_rejects_names(self):
        for name in ("alice/v1", "alice/v2", "bob/v3", "carol/v1", "starter-cpp"):
            self.bot(name)
        bots = batch.contestants([], self.root, round_robin=True)
        self.assertEqual([(b.name, b.version) for b in bots],
                         [("alice", "v2"), ("bob", "v3"), ("carol", "v1")])
        with self.assertRaisesRegex(ValueError, "omit explicit"):
            batch.contestants(["alice", "bob"], self.root, round_robin=True)

    def test_duplicate_version_names_require_explicit_selection(self):
        self.bot("alice/v1")
        self.bot("bob/v1")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            batch.resolve_bot("v1", self.root)
        self.assertEqual(batch.resolve_bot("alice", self.root).name, "alice")
        self.assertEqual(batch.resolve_bot("alice/v1", self.root).name, "alice")

    def test_two_versions_of_member_have_distinct_result_names(self):
        self.bot("alice/v1")
        self.bot("alice/v2")
        bots = batch.contestants(["alice/v1", "alice/v2"], self.root)
        self.assertEqual([b.name for b in bots], ["alice/v1", "alice/v2"])
        with self.assertRaisesRegex(ValueError, "same bot"):
            batch.contestants(["alice", "alice/v2"], self.root)

    def test_maps_are_validated_and_deduplicated(self):
        (self.root / "maps").mkdir()
        p = self.root / "maps/one.map26a"
        p.touch()
        self.assertEqual(batch.resolve_maps(["one", str(p)], self.root), [str(p)])
        with self.assertRaises(ValueError):
            batch.resolve_maps(["missing"], self.root)


class ScheduleTests(unittest.TestCase):
    def test_exact_game_count_balanced_adjacent_sides_and_coverage(self):
        for count in (1, 2, 5, 6, 17):
            plan = batch.schedule(["a", "b", "c"], count, 31)
            self.assertEqual(len(plan), count)
            for i in range(0, len(plan) - 1, 2):
                self.assertEqual(plan[i][0], plan[i + 1][0])
                self.assertNotEqual(plan[i][1], plan[i + 1][1])
            self.assertLessEqual(abs(sum(first for _, first in plan) - sum(not first for _, first in plan)), 1)
            self.assertEqual(len(set(plan[:6])), min(count, 6))

    def test_schedule_reproducible(self):
        self.assertEqual(batch.schedule(["a", "b", "c"], 20, 3), batch.schedule(["a", "b", "c"], 20, 3))


class ProbabilityTests(unittest.TestCase):
    def test_known_posteriors(self):
        self.assertEqual(batch.probability_better(0, 0), 0.5)
        self.assertAlmostEqual(batch.probability_better(1, 0), 0.75)
        self.assertAlmostEqual(batch.probability_better(3, 0), 0.9375)
        self.assertAlmostEqual(batch.probability_better(0, 3), 0.0625)
        self.assertEqual(batch.probability_better(50, 50), 0.5)

    def test_symmetry_monotonicity_and_large_samples(self):
        for wins, losses in ((3, 2), (90, 70), (1000, 980)):
            p = batch.probability_better(wins, losses)
            self.assertTrue(math.isfinite(p))
            self.assertGreater(p, 0.5)
            self.assertAlmostEqual(p + batch.probability_better(losses, wins), 1)
        self.assertGreater(batch.probability_better(8, 2), batch.probability_better(7, 2))

    def test_repeats_do_not_manufacture_probability_and_completion_order_does_not_matter(self):
        records = [result(2, False), result(1, True), result(3, False, first=False)]
        s = batch.summary(records)
        self.assertEqual((s["winsA"], s["winsB"]), (1, 2))
        self.assertEqual((s["uniqueScenarios"], s["uniqueWinsA"]), (2, 1))
        self.assertEqual(s["probabilityABetter"], 0.5)
        self.assertEqual(s["repeatedScenariosExcluded"], 1)

    def test_failed_runs_are_not_losses_or_probability_evidence(self):
        s = batch.summary([result(1), {"game": 2, "status": "failed"}])
        self.assertEqual((s["completed"], s["failed"], s["winsB"]), (1, 1, 0))
        self.assertAlmostEqual(s["probabilityABetter"], 0.75)
        self.assertEqual(batch.summary([])["winRateA"], None)

    def test_wilson_known_limits(self):
        low, high = batch.wilson(5, 10)
        self.assertAlmostEqual(low, 0.236593, places=5)
        self.assertAlmostEqual(high, 0.763407, places=5)
        self.assertEqual(batch.wilson(0, 0), [0.0, 1.0])

    def test_probability_display_does_not_round_to_certainty(self):
        self.assertEqual(batch.probability_percentage(0.99999999), ">99.9%")
        self.assertEqual(batch.probability_percentage(0.00000001), "<0.1%")
        self.assertEqual(batch.probability_percentage(0.5), "50.0%")


class RunnerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name) / "game"
        self.a, self.b = batch.Bot("alice", "v1", "/alice"), batch.Bot("bob", "v2", "/bob")

    def run_match(self):
        return batch.play("cambc", self.a, self.b, "/map.map26a", False, self.directory, 5)

    def test_swapped_side_normalizes_scores_faults_and_winner(self):
        def runner(command, **kwargs):
            self.assertEqual(command[2:4], ["/bob", "/alice"])
            (self.directory / "statistics.json").write_text(json.dumps({
                "outcome": "teamB", "round": 23, "botFaults": [2, 1],
                "teams": [{"team": 1, "submittedGems": 1000}, {"team": 0, "submittedGems": 700}]}))
            return subprocess.CompletedProcess(command, 0, "ok", "")
        with patch("batch.subprocess.run", side_effect=runner):
            r = self.run_match()
        self.assertEqual(r["status"], "completed")
        self.assertTrue(r["aWon"])
        self.assertEqual((r["gemsA"], r["gemsB"], r["faultsA"], r["faultsB"]), (1000, 700, 1, 2))

    def test_runner_failure_recorded_with_log(self):
        with patch("batch.subprocess.run", return_value=subprocess.CompletedProcess([], 1, "", "broken")):
            r = self.run_match()
        self.assertEqual(r["status"], "failed")
        self.assertEqual((self.directory / "runner.log").read_text(), "broken")

    def test_timeout_keeps_partial_output(self):
        with patch("batch.subprocess.run", side_effect=subprocess.TimeoutExpired([], 5, output=b"partial", stderr=b"error")):
            r = self.run_match()
        self.assertIn("Timed out", r["error"])
        self.assertEqual((self.directory / "runner.log").read_text(), "partialerror")

    def test_incomplete_statistics_not_scored_as_loss(self):
        def runner(command, **kwargs):
            (self.directory / "statistics.json").write_text(json.dumps({"outcome": "unfinished"}))
            return subprocess.CompletedProcess(command, 0, "", "")
        with patch("batch.subprocess.run", side_effect=runner):
            r = self.run_match()
        self.assertEqual(r["status"], "failed")


class ReplayNamingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name).resolve()
        self.a = batch.Bot("jame", "v1", "/bots/jame/v1")
        self.b = batch.Bot("simon", "v5", "/bots/simon/v5")

    def record(self, a_first=True):
        source = self.directory / "v1-vs-v5-1234.repl26a"
        source.write_bytes(b"unchanged replay contents")
        return {**result(1, won=False, first=a_first, map_path="swirl"),
                "gemsA": 286, "gemsB": 1038, "rounds": 583,
                "directory": str(self.directory), "replays": [str(source)]}

    def test_names_include_members_versions_map_sides_scores_winner_and_round(self):
        r = self.record()
        batch.rename_replays(self.a, self.b, r)
        p = Path(r["replays"][0])
        self.assertEqual(p.name, "game-0001__swirl__A-jame-v1-286__B-simon-v5-1038__winner-simon-v5__r583.repl26a")
        self.assertEqual(p.read_bytes(), b"unchanged replay contents")
        # Refreshing labels is idempotent.
        batch.rename_replays(self.a, self.b, r)
        self.assertEqual(Path(r["replays"][0]), p)

    def test_swapped_sides_keep_scores_attached_to_correct_members(self):
        r = self.record(a_first=False)
        batch.rename_replays(self.a, self.b, r)
        self.assertIn("__A-simon-v5-1038__B-jame-v1-286__", r["replays"][0])

    def test_existing_destination_is_never_overwritten(self):
        r = self.record()
        destination = self.directory / "game-0001__swirl__A-jame-v1-286__B-simon-v5-1038__winner-simon-v5__r583.repl26a"
        destination.write_bytes(b"keep me")
        with self.assertRaises(FileExistsError):
            batch.rename_replays(self.a, self.b, r)
        self.assertEqual(destination.read_bytes(), b"keep me")
        self.assertTrue(Path(r["replays"][0]).exists())

    def test_portable_directory_names_and_distinct_member_versions(self):
        a = batch.Bot("jame/v1", "v1", "/bots/jame/v1")
        b = batch.Bot("jame/v2", "v2", "/bots/jame/v2")
        self.assertEqual(batch.bot_tag(a), "jame-v1")
        d = batch.game_directory(self.directory, 0, 3, a, b, "/maps/rushbait-v2.map26a", False)
        self.assertEqual(d.parent.name, "pair-01__jame-v1-vs-jame-v2")
        self.assertEqual(d.name, "game-0003__rushbait-v2__A-jame-v2__B-jame-v1")
        self.assertNotIn("/", batch.slug("../unsafe:name"))


class BatchFolderTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.a = batch.Bot("jame", "v1", "/bots/jame/v1")
        self.b = batch.Bot("simon", "v5", "/bots/simon/v5")
        self.started = "2026-10-17T12:49:50+00:00"

    def saved_run(self, name="batch-old-id", status="finished"):
        directory = self.root / name
        game_dir = directory / "pair-1/game-0001"
        game_dir.mkdir(parents=True)
        replay = game_dir / "old.repl26a"
        replay.write_bytes(b"original replay")
        (game_dir / "runner.log").write_text("original runner output")
        game = result(1, won=False, map_path="/maps/swirl.map26a", map="swirl", gemsA=286,
                      gemsB=1038, rounds=583, directory=str(game_dir), replays=[str(replay)],
                      command=["cambc", "run", self.a.path, self.b.path, "-o", str(game_dir),
                               "--statistics", str(game_dir / "statistics.json")])
        payload = {"started": self.started, "status": status, "gamesPerPair": 1,
                   "maps": ["/maps/swirl.map26a"], "bots": [vars(self.a), vars(self.b)],
                   "pairs": [{"a": "jame", "b": "simon", "requested": 1, "games": [game]}]}
        batch.save(payload, directory)
        return directory

    def test_cleanup_removes_only_bundles_and_preserves_results_and_logs(self):
        old = self.saved_run()
        before = json.loads((old / "results.json").read_text())
        stats = old / "pair-1/game-0001/statistics.json"
        stats.write_text('{"original": true}')
        self.assertEqual(batch.clear_old_replays(self.root, self.root / "new"), 1)
        after = json.loads((old / "results.json").read_text())
        self.assertEqual(before["standings"], after["standings"])
        self.assertEqual(before["pairs"][0]["summary"], after["pairs"][0]["summary"])
        game = after["pairs"][0]["games"][0]
        self.assertEqual(game["replays"], [])
        self.assertTrue(game["replaysClearedAt"])
        self.assertIn("Cleared by a newer batch", (old / "report.md").read_text())
        self.assertNotIn("[Replay 1]", (old / "report.md").read_text())
        self.assertEqual(stats.read_text(), '{"original": true}')
        self.assertEqual((stats.parent / "runner.log").read_text(), "original runner output")
        self.assertFalse(list(old.rglob("*.repl26a")))
        self.assertEqual(batch.clear_old_replays(self.root, self.root / "new"), 0)

    def test_cleanup_keeps_current_running_and_unmanaged_runs(self):
        current = self.saved_run("current")
        running = self.saved_run("running", status="running")
        unrelated = self.root / "downloaded.repl26a"
        unrelated.write_bytes(b"download")
        (self.root / "unrelated").mkdir()
        (self.root / "unrelated/results.json").write_text('{"status":"finished"}')
        self.assertEqual(batch.clear_old_replays(self.root, current), 0)
        self.assertEqual(len(list(current.rglob("*.repl26a"))), 1)
        self.assertEqual(len(list(running.rglob("*.repl26a"))), 1)
        self.assertEqual(unrelated.read_bytes(), b"download")

    def test_cleanup_does_not_follow_links_or_manifest_paths_outside_run(self):
        old = self.saved_run()
        external = self.root / "external.repl26a"
        external.write_bytes(b"keep")
        (old / "linked.repl26a").symlink_to(external)
        (self.root / "linked-run").symlink_to(old, target_is_directory=True)
        payload = json.loads((old / "results.json").read_text())
        payload["pairs"][0]["games"][0]["replays"].append(str(external))
        batch.save(payload, old)
        self.assertEqual(batch.clear_old_replays(self.root, self.root / "new"), 1)
        self.assertEqual(external.read_bytes(), b"keep")
        self.assertTrue((old / "linked.repl26a").is_symlink())

    def test_cleanup_skips_linked_reports_and_malformed_batches(self):
        old = self.saved_run()
        outside = self.root / "external.md"
        outside.write_text("keep")
        (old / "report.md").unlink()
        (old / "report.md").symlink_to(outside)
        malformed = self.root / "malformed"
        malformed.mkdir()
        (malformed / "results.json").write_text('{"status":"finished","bots":[{}],"pairs":[{}]}')
        (malformed / "keep.repl26a").touch()
        self.assertEqual(batch.clear_old_replays(self.root, self.root / "new"), 0)
        self.assertEqual(outside.read_text(), "keep")
        self.assertTrue((malformed / "keep.repl26a").exists())

    def test_cli_clears_by_default_opt_out_and_build_failure_preserve_replays(self):
        for name, flags, build_code, should_keep in (
                ("default", [], 0, False),
                ("opt-out", ["--keep-old-replays"], 0, True),
                ("failed-build", [], 1, True)):
            with self.subTest(name=name):
                parent = self.root / name
                old = self.saved_run(name + "/old")
                output = parent / "new"
                completed = result(1, gemsA=12, gemsB=0, rounds=10, replays=[])
                build = subprocess.CompletedProcess([], build_code, "build output", "")
                with (patch.object(batch, "contestants", return_value=[self.a, self.b]),
                      patch.object(batch, "resolve_maps", return_value=["map"]),
                      patch.object(batch.subprocess, "run", return_value=build),
                      patch.object(batch, "play", return_value=completed),
                      redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO())):
                    args = ["--round-robin", "--games", "1", "--cambc", "fake-cli",
                            "--out", str(output), *flags]
                    if build_code:
                        with self.assertRaises(SystemExit) as error:
                            batch.main(args)
                        self.assertEqual(error.exception.code, 2)
                    else:
                        self.assertEqual(batch.main(args), 0)
                self.assertEqual(bool(list(old.rglob("*.repl26a"))), should_keep)

    def test_names_describe_matchup_versions_size_maps_and_time(self):
        self.assertEqual(batch.batch_name([self.a, self.b], 20, ["/maps/swirl.map26a"], self.started),
                         "jame-v1-vs-simon-v5__20-games__swirl__2026-10-17_124950-UTC")
        name = batch.batch_name([self.a, self.b, batch.Bot("daniel", "v5", "x")],
                                34, [f"map{i}" for i in range(17)], self.started)
        self.assertIn("round-robin__jame-v1_simon-v5_daniel-v5__34-games-per-pair__17-maps", name)

    def test_migration_preserves_bytes_updates_all_links_and_is_idempotent(self):
        old = self.saved_run()
        new = batch.rename_saved_batch(old)
        self.assertFalse(old.exists())
        game = json.loads((new / "results.json").read_text())["pairs"][0]["games"][0]
        self.assertEqual(Path(game["directory"]).name, "game-0001__swirl__A-jame-v1__B-simon-v5")
        self.assertEqual(Path(game["replays"][0]).read_bytes(), b"original replay")
        self.assertEqual((Path(game["directory"]) / "runner.log").read_text(), "original runner output")
        self.assertEqual(game["command"][2:4], [self.a.path, self.b.path])
        self.assertEqual(game["command"][-1], str(Path(game["directory"]) / "statistics.json"))
        for filename in ("results.json", "report.md", "games.csv"):
            self.assertNotIn(str(old), (new / filename).read_text())
        self.assertIn(f"{new.name}/report.md", (self.root / "index.md").read_text())
        self.assertEqual(batch.rename_saved_batch(new), new)

    def test_collision_refused_before_any_files_move(self):
        old = self.saved_run()
        destination = old.with_name(batch.batch_name([self.a, self.b], 1, ["swirl"], self.started))
        destination.mkdir()
        with self.assertRaises(FileExistsError):
            batch.rename_saved_batch(old)
        self.assertEqual((old / "pair-1/game-0001/old.repl26a").read_bytes(), b"original replay")
        self.assertNotEqual(batch.unused_run_directory(destination), destination)


if __name__ == "__main__":
    unittest.main()
