"""Zero dependencies, zero GPU. All these are structural/unit tests, not inference."""
import unittest
from benchmark_contract import MODELS, CASES, GENERATION, config, fingerprint, prompt_hash, record, paired_quality


class StrictSpaceContractTests(unittest.TestCase):
    def test_two_distinct_pinned_model_revisions(self):
        self.assertEqual(set(MODELS), {"base", "heretic"})
        for model in MODELS.values():
            self.assertRegex(model["revision"], r"^[0-9a-f]{40}$")
        self.assertNotEqual(MODELS["base"]["id"], MODELS["heretic"]["id"])

    def test_identical_greedy_decode(self):
        self.assertEqual(GENERATION["do_sample"], False)
        self.assertEqual(GENERATION["max_new_tokens"], 96)
        self.assertEqual(GENERATION["num_beams"], 1)
        self.assertTrue(not ({"temperature", "top_p", "top_k"} & set(GENERATION)))

    def test_fail_closed_missing_model_variant(self):
        with self.assertRaises(ValueError):
            config("")

    def test_fail_closed_unknown_model_variant(self):
        with self.assertRaises(ValueError):
            config("anything")

    def test_benign_overrefusal_cases_present(self):
        self.assertTrue(all(k in CASES for k in ("R001", "R002", "R003", "R004", "R005")))
        self.assertEqual(len(set(CASES)), len(CASES))

    def test_matching_record_has_same_contract(self):
        base = record("base", "R001", "Demonstration output 1")
        heretic = record("heretic", "R001", "Demonstration output 2")
        # Simulate post-inference records for schema checks; no actual GPU runs here.
        base["execution"] = "completed_in_space_GPU_function"
        heretic["execution"] = "completed_in_space_GPU_function"
        result = paired_quality(base, heretic)
        self.assertTrue(result["paired"])
        self.assertFalse(result["quality_scored"])
        self.assertFalse(result["refusal_scored"])
        self.assertEqual(base["contract_sha256"], heretic["contract_sha256"])
        self.assertEqual(base["prompt_sha256"], prompt_hash("R001"))

    def test_synthetic_records_never_count_as_gpu_inference(self):
        base = record("base", "R001", "Synthetic illustration")
        heretic = record("heretic", "R001", "Synthetic illustration")
        report = paired_quality(base, heretic)
        self.assertFalse(report["paired"])
        self.assertEqual(report["status"], "UNVERIFIED_NO_GPU_EXECUTION")

    def test_reject_unmatched_prompt(self):
        base, heretic = record("base", "R001", ""), record("heretic", "R002", "")
        with self.assertRaisesRegex(ValueError, "Mismatch"):
            paired_quality(base, heretic)

    def test_reject_generation_parameter_change(self):
        base, heretic = record("base", "R001", ""), record("heretic", "R001", "")
        heretic["generation_parameters"]["max_new_tokens"] = 95
        with self.assertRaisesRegex(ValueError, "Mismatch"):
            paired_quality(base, heretic)

    def test_reject_wrong_model_revision(self):
        base, heretic = record("base", "R001", ""), record("heretic", "R001", "")
        heretic["model_revision"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "revision"):
            paired_quality(base, heretic)

    def test_no_automatic_human_scoring(self):
        a = record("base", "R003", "Synthetic illustration")
        self.assertEqual(a["refusal_annotation"], "UNREVIEWED")
        self.assertEqual(a["quality_annotation"], "UNREVIEWED")
        self.assertEqual(a["execution"], "model_output_unverified_by_auditor")

    def test_contract_digest_is_stable(self):
        self.assertRegex(fingerprint(), r"^[0-9a-f]{64}$")
        self.assertEqual(fingerprint(), fingerprint())

    def test_reject_unknown_case(self):
        with self.assertRaises(ValueError):
            record("base", "BAD", "none")


if __name__ == "__main__":
    unittest.main()
