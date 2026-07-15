# Synthetic Case: Condition Signal to Durable Collateral Receipt

This fictional walkthrough shows how the three draft schemas can describe one reconciliation path. It contains no real property, owner, occupant, valuer, credential, signature, or financial account.

The hashes representing a private evidence bundle are synthetic placeholders. The proof value is explicitly non-cryptographic. Only the SHA-256 reference from `collateral-update.json` to the exact bytes of `valuation-attestation.json` is calculated from a file in this repository.

## Scenario

1. A scheduled inspection of a fictional real-estate asset records a potential condition deterioration signal. Six items were captured directly and one supporting item was uploaded manually.
2. The private evidence workflow closes a bundle and exposes only its identifier, timestamps, counts, condition signal, and synthetic commitments.
3. An illustrative authorized valuer reviews information outside this repository and issues an accepted valuation attestation for **EUR 240,000.00**. The repository does not perform that valuation.
4. A separate illustrative collateral policy applies a **25% haircut** and recognizes **EUR 180,000.00**. The policy decision is separate from the appraisal value.
5. A fictional collateral ledger confirms the update and returns a durable receipt identifier.

The `reduce_recognized_value` decision assumes that the fictional ledger previously recognized a higher amount. That earlier ledger record is outside this walkthrough, which begins at the refresh trigger.

## Files

| File | Boundary represented |
|---|---|
| [`condition-evidence.json`](condition-evidence.json) | Physical inspection workflow → private evidence commitment |
| [`valuation-attestation.json`](valuation-attestation.json) | Evidence commitment → versioned valuation issued by an authorized party |
| [`collateral-update.json`](collateral-update.json) | Accepted valuation → separate policy decision → durable ledger receipt |

## Relationships to inspect

- All three records use `asset:synthetic:seville:001`.
- The valuation references the exact evidence-bundle identifier, root commitment, observation time, and capture counts in the condition record.
- Timestamps follow `observed_at ≤ valuation_at ≤ issued_at ≤ decided_at ≤ submitted_at ≤ confirmed_at`.
- The collateral update references an `accepted` attestation that has not expired at decision time.
- `240000.00 × (1 − 2500 / 10000) = 180000.00`; this is an illustrative policy haircut, not a valuation calculation.
- `valuation_reference.attestation_hash_sha256` is the SHA-256 hash of the exact `valuation-attestation.json` file bytes.

To verify the last relationship on macOS or Linux:

```bash
shasum -a 256 valuation-attestation.json
```

## What this does not demonstrate

- collection or truthfulness of raw evidence;
- property appraisal methodology;
- legal title, lien priority, custody, or enforceability;
- a valid professional credential or cryptographic signature;
- encryption, selective disclosure, or privacy proofs;
- collateral-policy authorization;
- a live blockchain, custody platform, lender, registry, or external ledger.

The repository-level [limitations](../../LIMITATIONS.md) apply in full.
