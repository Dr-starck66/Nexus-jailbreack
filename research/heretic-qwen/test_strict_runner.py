"""Test strict authenticated runner without network, token or GPU."""
import unittest
from unittest.mock import patch
from strict_runner import run, validate_space, parse_stream, RejectRedirect
from strict_space.benchmark_contract import record


class StrictRunnerTests(unittest.TestCase):
    def test_dry_run_never_uses_network(self):
        with patch("strict_runner.request_case", side_effect=AssertionError("NETWORK USED")):
            r = run("R001", live=False)
        self.assertEqual(r["status"], "DRY_RUN")
        self.assertEqual(r["authentication"], "not_used_in_dry_run")

    def test_live_denied_if_no_token(self):
        with patch("strict_runner.request_case", side_effect=AssertionError("NETWORK USED")):
            with self.assertRaisesRegex(ValueError, "HF_TOKEN"):
                run("R001", "https://base.hf.space", "https://heretic.hf.space", live=True, token="")

    def test_reject_non_https_url(self):
        with self.assertRaises(ValueError):
            validate_space("http://owner.hf.space")

    def test_reject_credentials_and_query(self):
        for bad in ("https://user:pwd@owner.hf.space", "https://owner.hf.space/?x=1",
                    "https://owner.hf.space.example.com"):
            with self.assertRaises(ValueError):
                validate_space(bad)

    def test_reject_same_space(self):
        with self.assertRaisesRegex(ValueError, "differ"):
            run("R001", "https://same.hf.space", "https://same.hf.space", live=True, token="test")

    def test_response_unwrapped_from_sse(self):
        self.assertEqual(parse_stream('event: complete\ndata: [{"variant": "base"}]\n\n'), {"variant": "base"})

    def test_sse_error_is_not_pass(self):
        with self.assertRaisesRegex(RuntimeError, "quota"):
            parse_stream('event: error\ndata: {"error": "quota exceeded"}\n\n')

    def test_redirect_never_forwards_auth(self):
        with self.assertRaisesRegex(ValueError, "Redirect forbidden"):
            RejectRedirect().redirect_request(None, None, 302, "Moved", {}, "https://other.hf.space")

    def test_mismatched_model_pair_is_rejected(self):
        with patch("strict_runner.request_case", side_effect=[
            record("base", "R001", "fake response"),
            record("heretic", "R001", "fake response"),
        ]):
            with self.assertRaises(ValueError):
                run("R001", "https://base.hf.space", "https://heretic.hf.space", live=True, token="test")

    def test_mock_response_stays_unverified(self):
        rows = [record("heretic", "R001", "synthetic"), record("base", "R001", "synthetic")]
        with patch("strict_runner.request_case", side_effect=rows):
            r = run("R001", "https://base.hf.space", "https://heretic.hf.space", live=True, token="test")
        self.assertEqual(r["status"], "UNVERIFIED_NO_GPU_EXECUTION")
        self.assertFalse(r["paired_validation"]["paired"])


if __name__ == "__main__":
    unittest.main()
