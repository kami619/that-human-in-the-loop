import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(__file__))
import update_model_leaderboards as mod


class TestDeepSWEProcessing(unittest.TestCase):
    def test_best_effort_per_model_is_ranked(self):
        data = {
            "rows": [
                {"model": "gpt-5", "source": "deep-swe", "pass_rate": 0.7, "reasoning_effort": "low"},
                {"model": "gpt-5", "source": "deep-swe", "pass_rate": 0.8, "reasoning_effort": "high"},
                {"model": "claude-opus", "source": "deep-swe", "pass_rate": 0.75},
            ]
        }
        result = mod.process_deepswe(data)
        self.assertEqual([row["model"] for row in result], ["gpt-5", "claude-opus"])
        self.assertEqual(result[0]["reasoning_effort"], "high")
        self.assertEqual(result[0]["pass_rate"], 80.0)


class TestArtificialAnalysisProcessing(unittest.TestCase):
    def test_nested_fields_are_normalized(self):
        data = {"data": [
            {
                "name": "Model A",
                "model_creator": {"name": "Provider A"},
                "evaluations": {"artificial_analysis_intelligence_index": 91.2},
                "artificial_analysis_intelligence_index_cost": {
                    "cost_per_task": {"total_cost": 0.42}
                },
                "performance": {
                    "median_output_tokens_per_second": 100,
                    "median_time_to_first_token_seconds": 1.2,
                },
            },
            {"name": "Missing score", "evaluations": {}},
        ]}
        result = mod.process_artificial_analysis(data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["rank"], 1)
        self.assertEqual(result[0]["intelligence_index"], 91.2)
        self.assertEqual(result[0]["provider"], "Provider A")
        self.assertEqual(result[0]["cost_per_task_usd"], 0.42)


if __name__ == "__main__":
    unittest.main()
