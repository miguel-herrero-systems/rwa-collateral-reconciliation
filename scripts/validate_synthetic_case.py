#!/usr/bin/env python3
"""Validate the repository's narrow, synthetic reconciliation fixture."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASE_DIR = ROOT / "examples" / "synthetic-case"
DEFAULT_SCHEMA_DIR = ROOT / "schemas"

RECORD_SCHEMAS = {
    "condition-evidence.json": "condition-evidence.schema.json",
    "valuation-attestation.json": "valuation-attestation.schema.json",
    "collateral-update.json": "collateral-update.schema.json",
}


class ReconciliationError(ValueError):
    """Raised when the synthetic records fail a cross-record check."""


def _read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise ReconciliationError(f"cannot read valid JSON from {path}: {exc}") from exc


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReconciliationError(message)


def _timestamp(label: str, value: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as exc:
        raise ReconciliationError(f"{label} is not a valid ISO-8601 timestamp") from exc
    _require(timestamp.tzinfo is not None, f"{label} must include a timezone")
    return timestamp


def _validate_schemas(
    records: dict[str, dict[str, Any]], schema_dir: Path
) -> None:
    for record_name, schema_name in RECORD_SCHEMAS.items():
        schema = _read_json(schema_dir / schema_name)
        Draft202012Validator.check_schema(schema)
        errors = sorted(
            Draft202012Validator(schema).iter_errors(records[record_name]),
            key=lambda error: list(error.absolute_path),
        )
        if errors:
            error = errors[0]
            location = ".".join(str(part) for part in error.absolute_path) or "<root>"
            raise ReconciliationError(
                f"{record_name} fails {schema_name} at {location}: {error.message}"
            )


def validate_case(
    case_dir: Path = DEFAULT_CASE_DIR, schema_dir: Path = DEFAULT_SCHEMA_DIR
) -> dict[str, str]:
    """Validate the bundled record shapes and selected continuity invariants."""

    case_dir = Path(case_dir)
    schema_dir = Path(schema_dir)
    records = {name: _read_json(case_dir / name) for name in RECORD_SCHEMAS}
    _validate_schemas(records, schema_dir)

    condition = records["condition-evidence.json"]
    valuation = records["valuation-attestation.json"]
    update = records["collateral-update.json"]

    _require(
        condition["asset"]["asset_id"]
        == valuation["asset"]["asset_id"]
        == update["asset"]["asset_id"],
        "asset_id differs across records",
    )
    _require(
        condition["asset"]["unit_id"]
        == valuation["asset"]["unit_id"]
        == update["asset"]["unit_id"],
        "unit_id differs across records",
    )
    _require(
        condition["asset"]["jurisdiction"] == valuation["asset"]["jurisdiction"],
        "jurisdiction differs between evidence and valuation",
    )
    _require(
        condition["asset"]["asset_class"] == valuation["asset"]["asset_class"],
        "asset_class differs between evidence and valuation",
    )

    evidence = valuation["evidence"]
    _require(
        evidence["evidence_bundle_id"] == condition["evidence_bundle_id"],
        "valuation references a different evidence bundle",
    )
    _require(
        evidence["root_hash_sha256"] == condition["integrity"]["root_hash_sha256"],
        "valuation references a different evidence root hash",
    )
    for field in ("observed_at", "direct_capture_count", "manual_upload_count"):
        _require(
            evidence[field] == condition["capture"][field],
            f"valuation evidence {field} differs from condition record",
        )

    _require(
        update["valuation_reference"]["attestation_id"]
        == valuation["attestation_id"],
        "collateral update references a different attestation",
    )
    _require(
        valuation["lifecycle"]["status"] == "accepted"
        and update["valuation_reference"]["attestation_status"] == "accepted",
        "collateral update requires an accepted attestation",
    )
    _require(
        condition["lifecycle"]["status"] == "closed",
        "valuation requires a closed evidence bundle",
    )

    started_at = _timestamp("capture.started_at", condition["capture"]["started_at"])
    observed_at = _timestamp("capture.observed_at", condition["capture"]["observed_at"])
    closed_at = _timestamp("capture.closed_at", condition["capture"]["closed_at"])
    record_created_at = _timestamp(
        "condition.lifecycle.created_at", condition["lifecycle"]["created_at"]
    )
    valuation_at = _timestamp("valuation.valuation_at", valuation["valuation"]["valuation_at"])
    issued_at = _timestamp("valuation.lifecycle.issued_at", valuation["lifecycle"]["issued_at"])
    expires_at = _timestamp("valuation.lifecycle.expires_at", valuation["lifecycle"]["expires_at"])
    decided_at = _timestamp("policy_decision.decided_at", update["policy_decision"]["decided_at"])
    submitted_at = _timestamp(
        "ledger_update.submitted_at", update["ledger_update"]["submitted_at"]
    )
    confirmed_at = _timestamp(
        "ledger_update.confirmed_at", update["ledger_update"]["confirmed_at"]
    )

    _require(
        started_at <= observed_at <= closed_at <= record_created_at,
        "condition timestamps are not monotonic",
    )
    _require(
        observed_at <= valuation_at <= issued_at <= decided_at,
        "evidence, valuation, issuance, and decision timestamps are not monotonic",
    )
    _require(decided_at < expires_at, "attestation is expired at decision time")
    _require(
        decided_at <= submitted_at <= confirmed_at,
        "decision, submission, and confirmation timestamps are not monotonic",
    )
    _require(
        update["ledger_update"]["status"] == "confirmed"
        and bool(update["ledger_update"].get("receipt_id")),
        "synthetic ledger update is not confirmed by a receipt",
    )

    try:
        appraised = Decimal(valuation["valuation"]["amount"])
        haircut = Decimal(update["policy_decision"]["haircut_bps"]) / Decimal(10000)
        recognized = Decimal(
            update["policy_decision"]["recognized_collateral_value"]["amount"]
        )
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ReconciliationError("valuation or haircut is not a valid decimal") from exc
    _require(
        valuation["valuation"]["currency"]
        == update["policy_decision"]["recognized_collateral_value"]["currency"],
        "valuation and recognized collateral use different currencies",
    )
    _require(
        appraised * (Decimal(1) - haircut) == recognized,
        "recognized collateral does not reconcile with the declared haircut",
    )

    attestation_hash = hashlib.sha256(
        (case_dir / "valuation-attestation.json").read_bytes()
    ).hexdigest()
    _require(
        update["valuation_reference"]["attestation_hash_sha256"] == attestation_hash,
        "collateral update attestation hash does not match the valuation file",
    )

    _require(
        condition["privacy"]["raw_evidence_public"] is False,
        "condition exposes raw evidence",
    )
    _require(
        valuation["privacy"]["raw_evidence_public"] is False,
        "valuation exposes raw evidence",
    )
    _require(update["privacy"]["raw_evidence_included"] is False, "update includes raw evidence")

    return {
        "asset_id": condition["asset"]["asset_id"],
        "attestation_id": valuation["attestation_id"],
        "recognized_collateral": f"{recognized} {valuation['valuation']['currency']}",
        "attestation_hash_sha256": attestation_hash,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate the repository's synthetic reconciliation fixture."
    )
    parser.add_argument("--case-dir", type=Path, default=DEFAULT_CASE_DIR)
    parser.add_argument("--schema-dir", type=Path, default=DEFAULT_SCHEMA_DIR)
    args = parser.parse_args()

    try:
        result = validate_case(args.case_dir, args.schema_dir)
    except ReconciliationError as exc:
        print(f"FAIL: {exc}")
        return 1

    print("PASS: synthetic reconciliation fixture")
    for key, value in result.items():
        print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
