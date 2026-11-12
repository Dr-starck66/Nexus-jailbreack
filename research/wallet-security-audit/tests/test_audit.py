"""No production wallet, network, or third-party dependencies required."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from audit import assess, AuditError, SCHEMA, markdown


class WalletAuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "ASTRA_SCOPE.json").write_text(json.dumps({"mode": "synthetic", "assessment_id": "synthetic-001"}))
        self.manifest = {"schema": SCHEMA, "assessment_id": "synthetic-001", "mode": "synthetic",
                         "app_id": "example.test.wallet", "controls": {}}
        self.fact("secret_storage", "plaintext_file")
        self.fact("backup_exclusion", False)
        self.fact("secrets_in_logs", True)
        self.fact("shared_app_group_secrets", False)
        self.fact("file_protection_complete", True)

    def fact(self, key, value, with_evidence=True):
        entry = {"value": value}
        if with_evidence:
            path = self.root / (key + ".txt")
            path.write_text("SANITIZED: demonstration only: " + key)
            entry.update({"evidence_path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        self.manifest["controls"][key] = entry

    def test_high_risk_with_evidence(self):
        out = assess(self.manifest, self.root)
        self.assertEqual((out["evidence_gate"], out["risk_screen"]), ("PASS", "HIGH_INDICATIVE"))
        self.assertEqual(out["ios_device_validation"], "UNVERIFIED")
        self.assertFalse(out["secrets_read"])

    def test_no_assurance_from_keychain_declaration(self):
        self.fact("secret_storage", "secure_enclave")
        self.fact("secrets_in_logs", False)
        self.fact("backup_exclusion", True)
        r = assess(self.manifest, self.root)
        self.assertEqual(r["risk_screen"], "LOWER_INDICATIVE_NOT_SAFE_CLAIM")
        self.assertEqual(r["ios_device_validation"], "UNVERIFIED")

    def test_missing_evidence_fails_closed_to_unverified(self):
        self.fact("secret_storage", "keychain", with_evidence=False)
        self.fact("secrets_in_logs", False)
        r = assess(self.manifest, self.root)
        self.assertEqual((r["evidence_gate"], r["risk_screen"]), ("PARTIAL", "UNVERIFIED"))

    def test_invalid_digest_rejected(self):
        self.manifest["controls"]["secret_storage"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(AuditError, "mismatch"):
            assess(self.manifest, self.root)

    def test_evidence_traversal_rejected(self):
        self.manifest["controls"]["secret_storage"]["evidence_path"] = "../private.txt"
        with self.assertRaisesRegex(AuditError, "traversal"):
            assess(self.manifest, self.root)

    def test_symlink_rejected(self):
        target = self.root / "secret_storage.txt"
        target.unlink()
        external = self.root.parent / ("external-" + self.root.name)
        external.write_text("dummy")
        self.addCleanup(lambda: external.unlink(missing_ok=True))
        target.symlink_to(external)
        with self.assertRaises(AuditError):
            assess(self.manifest, self.root)

    def test_out_of_scope_rejected(self):
        (self.root / "ASTRA_SCOPE.json").write_text('{"mode":"synthetic","assessment_id":"someone-else"}')
        with self.assertRaisesRegex(AuditError, "mismatched"):
            assess(self.manifest, self.root)

    def test_authorized_lab_requires_reference(self):
        (self.root / "ASTRA_SCOPE.json").write_text('{"mode":"authorized_lab","assessment_id":"synthetic-001"}')
        self.manifest["mode"] = "authorized_lab"
        with self.assertRaisesRegex(AuditError, "authorization"):
            assess(self.manifest, self.root)

    def test_unknown_not_green(self):
        self.fact("secret_storage", "unknown")
        self.fact("secrets_in_logs", False)
        r = assess(self.manifest, self.root)
        self.assertEqual(r["risk_screen"], "UNVERIFIED")

    def test_boolean_type_guard(self):
        self.fact("backup_exclusion", 1)
        with self.assertRaisesRegex(AuditError, "Invalid value"):
            assess(self.manifest, self.root)

    def test_missing_control_rejected(self):
        self.manifest["controls"].pop("secrets_in_logs")
        with self.assertRaisesRegex(AuditError, "mandatory"):
            assess(self.manifest, self.root)

    def test_symlink_root_rejected(self):
        alias = self.root.parent / ("alias-" + self.root.name)
        alias.symlink_to(self.root, target_is_directory=True)
        self.addCleanup(lambda: alias.unlink(missing_ok=True))
        with self.assertRaisesRegex(AuditError, "Symlink root"):
            assess(self.manifest, alias)

    def test_report_never_contains_secret_contents(self):
        target = self.root / "secret_storage.txt"
        target.write_text("CANARY-DO-NOT-EMIT-123")
        self.manifest["controls"]["secret_storage"]["sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
        r = assess(self.manifest, self.root)
        self.assertNotIn("CANARY-DO-NOT-EMIT-123", json.dumps(r) + markdown(r))


if __name__ == "__main__":
    unittest.main()
