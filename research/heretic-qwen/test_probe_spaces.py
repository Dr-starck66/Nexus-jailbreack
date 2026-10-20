"""Negative controls for the public demo runner (no network, no GPU)."""
import os
import unittest
from unittest.mock import patch
from probe_spaces import CASES, SPACES, get_headers, decode_sse, parse_response, evaluate


class RunnerTests(unittest.TestCase):
    def test_token_not_required(self):
        with patch.dict(os.environ, {"HF_TOKEN": ""}):
            self.assertNotIn("Authorization", get_headers())

    def test_optional_free_account_authorization_header(self):
        with patch.dict(os.environ, {"HF_TOKEN": "fake-test-value"}):
            self.assertEqual(get_headers()["Authorization"], "Bearer fake-test-value")
            audit = evaluate(1, False, ["R001"])
            self.assertEqual(audit["zero_gpu_authentication"], "free_account_token_supplied")
            self.assertNotIn("fake-test-value", str(audit))

    def test_explicit_dry_run(self):
        report = evaluate(2, False)
        self.assertEqual(report["status"], "DRY_RUN")
        self.assertEqual(report["paired_completed"], 0)
        self.assertEqual(len(report["cases"]), 2)
        self.assertTrue(all(r["status"] == "NOT_RUN" for r in report["cases"]))

    def test_quota_blocks_classified(self):
        raw = 'event: error\ndata: {"error": "You have exceeded your ZeroGPU runs limit."}\n\n'
        result = parse_response("heretic", decode_sse(raw))
        self.assertEqual(result["status"], "quota_blocked")

    def test_complete_base(self):
        raw = 'event: generating\ndata: ["15", null]\n\nevent: complete\ndata: ["156", null]\n\n'
        self.assertEqual(parse_response("base", decode_sse(raw)), {"status": "complete", "answer": "156"})

    def test_complete_heretic_echo_removed(self):
        raw = 'event: complete\ndata: ["system\\nYou are a helpful assistant.\\nuser\\nQuestion\\nassistant\\n156", null]\n\n'
        self.assertEqual(parse_response("heretic", decode_sse(raw)), {"status": "complete", "answer": "156"})

    def test_no_fake_pass_on_missing_complete(self):
        result = parse_response("heretic", decode_sse('event: generating\ndata: ["partial", null]\n\n'))
        self.assertEqual(result["status"], "incomplete")

    def test_unexpected_shape_fails(self):
        result = parse_response("base", decode_sse('event: complete\ndata: {"raw": "fake"}\n\n'))
        self.assertEqual(result["status"], "error")

    def test_only_benign_prompts(self):
        self.assertEqual(len(CASES), 10)
        self.assertEqual(set(SPACES), {"base", "heretic"})
        self.assertTrue(all(cid.startswith("B") and isinstance(prompt, str) for cid, prompt, _ in CASES))

    def test_overrefusal_case_is_selected_with_no_network(self):
        report = evaluate(1, False, ["R001"])
        self.assertEqual(report["status"], "DRY_RUN")
        self.assertEqual(report["cases"][0]["case_id"], "R001")
        self.assertEqual(report["cases"][0]["category"], "benign_overrefusal_probe")
        self.assertEqual(report["cases"][0]["refusal_label"], "HUMAN_REVIEW_REQUIRED")

    def test_refusal_measure_never_invented(self):
        report = evaluate(2, False, ["R002", "R003"])
        self.assertEqual(report["paired_completed"], 0)
        self.assertTrue(all(row["refusal_label"] == "HUMAN_REVIEW_REQUIRED" for row in report["cases"]))

    def test_no_injection_scores(self):
        report = evaluate(5, False)
        self.assertNotIn("injection_success_rate", report)
        self.assertEqual(report["paired_completed"], 0)


if __name__ == "__main__":
    unittest.main()
