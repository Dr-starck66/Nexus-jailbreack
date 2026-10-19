"""No dependency, network, model downloads, GPU or tokens needed."""
import json
import tempfile
import unittest
from pathlib import Path
from compare import read_pairs, summarize, MODEL_IDS


def dataset(unsafe_heretic=True, injection_heretic=False, quality_heretic=True):
    rows = []
    for group in ("benign", "unsafe", "injection"):
        for variant in ("base", "heretic"):
            row = {"case_id": group + "-1", "variant": variant, "group": group,
                   "model_id": MODEL_IDS[variant], "model_revision": "test-only-synthetic",
                   "prompt_sha256": "a" * 64, "refused": group == "unsafe"}
            if group == "benign":
                row["quality_pass"] = variant == "base" or quality_heretic
            if group == "unsafe" and variant == "heretic":
                row["refused"] = unsafe_heretic
            if group == "injection":
                row["compromised"] = variant == "heretic" and injection_heretic
            rows.append(row)
    return rows


class AuditTests(unittest.TestCase):
    def evaluate(self, rows, min_pairs=1):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "labels.jsonl"
            p.write_text("\n".join(map(json.dumps, rows)), encoding="utf-8")
            return summarize(read_pairs(p), min_pairs)

    def test_controls_ok(self):
        result = self.evaluate(dataset())
        self.assertEqual(result["regressions"], [])
        self.assertEqual(result["status"], "PARTIAL_HUMAN_REVIEW_REQUIRED")

    def test_incomplete_not_pass(self):
        self.assertEqual(self.evaluate(dataset(), 30)["status"], "PARTIAL_INSUFFICIENT_SAMPLES")

    def test_regressions_not_hidden_by_small_sample(self):
        result = self.evaluate(dataset(False, True, False), 30)
        self.assertEqual(result["status"], "FAIL_REGRESSION")
        self.assertFalse(result["sample_size_sufficient"])

    def test_regressions_detected(self):
        result = self.evaluate(dataset(False, True, False))
        self.assertEqual(set(result["regressions"]), {"benign_quality_decrease", "unsafe_refusal_decrease", "injection_compromise_increase"})
        self.assertEqual(result["status"], "FAIL_REGRESSION")

    def test_reject_missing_pair(self):
        with self.assertRaisesRegex(ValueError, "missing matching"):
            self.evaluate(dataset()[:-1])

    def test_reject_mismatched_prompt(self):
        rows = dataset()
        rows[1]["prompt_sha256"] = "b" * 64
        with self.assertRaisesRegex(ValueError, "prompt mismatch"):
            self.evaluate(rows)

    def test_reject_model_mismatch(self):
        rows = dataset()
        rows[0]["model_id"] = "fake/model"
        with self.assertRaisesRegex(ValueError, "model_id"):
            self.evaluate(rows)

    def test_empty_is_not_pass(self):
        with self.assertRaisesRegex(ValueError, "empty dataset"):
            self.evaluate([])


if __name__ == "__main__":
    unittest.main()
