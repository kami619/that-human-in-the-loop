"""
stdlib-only unit tests for update_bfcl_leaderboard.py
Run: python -m unittest functions/test_update_bfcl.py
"""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import update_bfcl_leaderboard as mod


class TestParseModelString(unittest.TestCase):
    def test_valid_input(self):
        model, type_ = mod.parse_model_string("Claude-Sonnet-4-5-20250929 (FC)")
        self.assertEqual(model, "Claude-Sonnet-4-5-20250929")
        self.assertEqual(type_, "FC")

    def test_no_parens(self):
        model, type_ = mod.parse_model_string("SomeModel")
        self.assertEqual(model, "SomeModel")
        self.assertEqual(type_, "Unknown")

    def test_fc_thinking(self):
        model, type_ = mod.parse_model_string("GPT-4o (FC thinking)")
        self.assertEqual(model, "GPT-4o")
        self.assertEqual(type_, "FC thinking")

    def test_whitespace_trimmed(self):
        model, _ = mod.parse_model_string("  My Model  (Prompt)")
        self.assertEqual(model, "My Model")


class TestProcessData(unittest.TestCase):
    HEADER = "Rank,Model,Organization,Overall Acc"

    def _csv(self, rows):
        return "\n".join([self.HEADER] + rows)

    def test_rank_order(self):
        csv_text = self._csv([
            "3,ModelC (FC),OrgA,87.0%",
            "1,ModelA (FC),OrgA,95.0%",
            "2,ModelB (FC),OrgA,91.0%",
        ])
        result = mod.process_data(csv_text)
        self.assertEqual([r['rank'] for r in result], [1, 2, 3])

    def test_top_n_truncation(self):
        rows = [f"{i},Model-{i} (FC),OrgA,{90 - i}.0%" for i in range(1, mod.TOP_N + 5)]
        result = mod.process_data(self._csv(rows))
        self.assertLessEqual(len(result), mod.TOP_N)

    def test_type_normalization_fc_thinking(self):
        csv_text = self._csv(["1,GPT-4 (FC thinking),OpenAI,95.0%"])
        result = mod.process_data(csv_text)
        self.assertEqual(result[0]['type'], 'FC')

    def test_type_normalization_prompt(self):
        csv_text = self._csv(["1,Model-X (Prompt),OrgB,80.0%"])
        result = mod.process_data(csv_text)
        self.assertEqual(result[0]['type'], 'Prompt')

    def test_accuracy_parsed_correctly(self):
        csv_text = self._csv(["1,ModelA (FC),OrgA,92.5%"])
        result = mod.process_data(csv_text)
        self.assertAlmostEqual(result[0]['accuracy'], 92.5)

    def test_bad_row_skipped(self):
        csv_text = self._csv([
            "1,ModelA (FC),OrgA,95.0%",
            "BAD_RANK,ModelB (FC),OrgA,notanumber%",
        ])
        result = mod.process_data(csv_text)
        self.assertEqual(len(result), 1)


class TestUpdateJsonFile(unittest.TestCase):
    def setUp(self):
        self._orig_path = mod.JSON_FILE_PATH
        self.tmp = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        )
        self.tmp.close()
        mod.JSON_FILE_PATH = self.tmp.name

    def tearDown(self):
        mod.JSON_FILE_PATH = self._orig_path
        os.unlink(self.tmp.name)

    def _write_existing(self, content):
        with open(self.tmp.name, 'w') as f:
            f.write(content)

    def _read_result(self):
        with open(self.tmp.name) as f:
            return json.load(f)

    def test_meta_fields_written(self):
        self._write_existing('{"meta": {}}')
        mod.update_json_file([])
        data = self._read_result()
        self.assertIn("source", data["meta"])
        self.assertIn("last_updated", data["meta"])
        self.assertIn("url", data["meta"])

    def test_existing_description_preserved(self):
        self._write_existing('{"meta": {"description": "Keep me"}}')
        mod.update_json_file([])
        data = self._read_result()
        self.assertEqual(data["meta"]["description"], "Keep me")

    def test_description_added_when_absent(self):
        self._write_existing('{"meta": {}}')
        mod.update_json_file([])
        data = self._read_result()
        self.assertIn("description", data["meta"])

    def test_leaderboard_written(self):
        self._write_existing('{"meta": {}}')
        lb = [{"rank": 1, "model": "Test", "provider": "X", "accuracy": 99.0, "type": "FC"}]
        mod.update_json_file(lb)
        data = self._read_result()
        self.assertEqual(data["leaderboard"], lb)

    def test_missing_file_creates_fresh(self):
        os.unlink(self.tmp.name)
        mod.update_json_file([])
        data = self._read_result()
        self.assertIn("meta", data)
        self.assertIn("source", data["meta"])

    def test_corrupt_json_recovers(self):
        self._write_existing("NOT_VALID_JSON{{{")
        mod.update_json_file([])  # should not raise
        data = self._read_result()
        self.assertIn("meta", data)


if __name__ == "__main__":
    unittest.main()
