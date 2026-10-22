"""Zero-network negative controls for free ZeroGPU bootstrap."""
import io
import pathlib
import tempfile
import unittest
from unittest.mock import MagicMock, patch
import bootstrap_zero_gpu as boot


class FakeHttpError(Exception):
    def __init__(self, status):
        self.response = type("Response", (), {"status_code": status})()
        super().__init__("simulated status")


class TestZeroGpuProvisioning(unittest.TestCase):
    def test_expected_names_and_free_hardware_only(self):
        entries = boot.plan("example")["spaces"]
        self.assertEqual(len(entries), 2)
        self.assertEqual(set(x["MODEL_VARIANT"] for x in entries), {"base", "heretic"})
        self.assertTrue(all(x["hardware"] == "zero-a10g" for x in entries))

    def test_missing_files_fails_before_network(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(boot, "FILES_ROOT", pathlib.Path(d)):
                with self.assertRaisesRegex(RuntimeError, "Missing deployment file"):
                    boot.apply(MagicMock(), "example")

    def test_existing_zero_gpu_never_overwritten(self):
        api = MagicMock()
        api.space_info.return_value.runtime.hardware = "zero-a10g"
        with self.assertRaisesRegex(RuntimeError, "intentionally refuse overwrite"):
            boot.apply(api, "example")
        api.create_repo.assert_not_called()
        api.upload_folder.assert_not_called()

    def test_existing_paid_space_rejected(self):
        api = MagicMock()
        api.space_info.return_value.runtime.hardware = "t4-medium"
        api.space_info.return_value.runtime.requested_hardware = "t4-medium"
        with self.assertRaisesRegex(RuntimeError, "not ZeroGPU"):
            boot.apply(api, "example")
        api.create_repo.assert_not_called()

    def test_forbidden_no_zero_gpu_confirmation(self):
        api = MagicMock()
        api.space_info.side_effect = FakeHttpError(404)
        api.get_space_runtime.return_value.requested_hardware = "cpu-basic"
        api.get_space_runtime.return_value.hardware = "cpu-basic"
        with self.assertRaisesRegex(RuntimeError, "ZeroGPU was not confirmed"):
            boot.apply(api, "example")
        api.upload_folder.assert_not_called()
        kwargs = api.create_repo.call_args.kwargs
        self.assertEqual(kwargs["space_hardware"], "zero-a10g")
        self.assertEqual(kwargs["repo_type"], "space")
        self.assertFalse(kwargs["private"])
        self.assertEqual(kwargs["space_variables"][0]["key"], "MODEL_VARIANT")

    def test_create_success_both_zero_gpu(self):
        api = MagicMock()
        api.space_info.side_effect = FakeHttpError(404)
        api.get_space_runtime.return_value.requested_hardware = "zero-a10g"
        api.get_space_runtime.return_value.hardware = "zero-a10g"
        results = boot.apply(api, "example")
        self.assertEqual(len(results), 2)
        self.assertEqual(api.create_repo.call_count, 2)
        self.assertEqual(api.upload_folder.call_count, 2)
        self.assertTrue(all(c.kwargs["space_hardware"] == "zero-a10g" for c in api.create_repo.call_args_list))

    def test_no_fallback_on_payment_error(self):
        api = MagicMock()
        api.space_info.side_effect = FakeHttpError(402)
        with self.assertRaises(FakeHttpError):
            boot.apply(api, "example")
        api.create_repo.assert_not_called()

    def test_plan_does_not_require_credentials(self):
        self.assertFalse(boot.plan()["paid_gpu_fallback"])
        self.assertEqual(boot.plan()["monthly_euro_spend"], 0)


if __name__ == "__main__":
    unittest.main()
