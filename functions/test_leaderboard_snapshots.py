"""Validate the checked-in dashboard leaderboard snapshots."""

import json
import os
import unittest


ROOT = os.path.dirname(os.path.dirname(__file__))


class TestLeaderboardSnapshots(unittest.TestCase):
    def _load(self, filename):
        with open(os.path.join(ROOT, filename), encoding="utf-8") as handle:
            return json.load(handle)

    def _assert_common_shape(self, data):
        self.assertIn("meta", data)
        self.assertIn("leaderboard", data)
        self.assertTrue(data["meta"]["source"])
        self.assertTrue(data["meta"]["url"].startswith("https://"))
        self.assertTrue(data["meta"]["last_updated"])
        self.assertGreaterEqual(len(data["leaderboard"]), 6)
        self.assertEqual([row["rank"] for row in data["leaderboard"][:6]], list(range(1, 7)))

    def test_deepswe_snapshot(self):
        data = self._load("deepswe-leaderboard.json")
        self._assert_common_shape(data)
        version = data["meta"]["version"]
        self.assertRegex(version, r"^v\d+\.\d+$", msg=f"unexpected version format: {version}")
        self.assertIsInstance(data["meta"]["tasks"], int)
        self.assertGreater(data["meta"]["tasks"], 0)
        self.assertTrue(all("pass_rate" in row for row in data["leaderboard"]))

    def test_artificial_analysis_snapshot(self):
        data = self._load("artificial-analysis-leaderboard.json")
        self._assert_common_shape(data)
        version = data["meta"]["version"]
        self.assertRegex(version, r"^\d+\.\d+$", msg=f"unexpected version format: {version}")
        self.assertTrue(all("intelligence_index" in row for row in data["leaderboard"]))


if __name__ == "__main__":
    unittest.main()
