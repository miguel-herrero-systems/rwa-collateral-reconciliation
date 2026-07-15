from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from validate_synthetic_case import ReconciliationError, validate_case  # noqa: E402


class SyntheticCaseTests(unittest.TestCase):
    def copy_case(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        target = Path(temporary.name) / "synthetic-case"
        shutil.copytree(ROOT / "examples" / "synthetic-case", target)
        return target

    @staticmethod
    def read(path: Path) -> dict:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)

    @staticmethod
    def write(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def synchronize_attestation_hash(self, case_dir: Path) -> None:
        valuation_path = case_dir / "valuation-attestation.json"
        update_path = case_dir / "collateral-update.json"
        update = self.read(update_path)
        update["valuation_reference"]["attestation_hash_sha256"] = hashlib.sha256(
            valuation_path.read_bytes()
        ).hexdigest()
        self.write(update_path, update)

    def test_bundled_case_is_valid(self) -> None:
        result = validate_case()
        self.assertEqual(result["recognized_collateral"], "180000.00 EUR")

    def test_changed_attestation_hash_is_rejected(self) -> None:
        case_dir = self.copy_case()
        update_path = case_dir / "collateral-update.json"
        update = self.read(update_path)
        update["valuation_reference"]["attestation_hash_sha256"] = "0" * 64
        self.write(update_path, update)

        with self.assertRaisesRegex(ReconciliationError, "hash does not match"):
            validate_case(case_dir)

    def test_expired_attestation_is_rejected(self) -> None:
        case_dir = self.copy_case()
        valuation_path = case_dir / "valuation-attestation.json"
        valuation = self.read(valuation_path)
        valuation["lifecycle"]["expires_at"] = "2026-07-16T10:59:00Z"
        self.write(valuation_path, valuation)
        self.synchronize_attestation_hash(case_dir)

        with self.assertRaisesRegex(ReconciliationError, "expired at decision time"):
            validate_case(case_dir)

    def test_inconsistent_haircut_arithmetic_is_rejected(self) -> None:
        case_dir = self.copy_case()
        update_path = case_dir / "collateral-update.json"
        update = self.read(update_path)
        update["policy_decision"]["recognized_collateral_value"]["amount"] = "180001.00"
        self.write(update_path, update)

        with self.assertRaisesRegex(ReconciliationError, "declared haircut"):
            validate_case(case_dir)


if __name__ == "__main__":
    unittest.main()
