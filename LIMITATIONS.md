# Limitations

This repository is an experimental reference model. Its purpose is to make boundaries and evidence states explicit, not to represent a deployable financial or valuation system.

## No valuation or appraisal

- It does not determine market value, mortgage lending value, replacement cost, or impairment.
- It does not infer value from photographs, observations, severity scores, or machine-learning output.
- It does not establish who is legally authorized to value a particular asset in a particular jurisdiction.

## No financial decision

- It does not calculate recognized collateral value, loan-to-value ratios, margin requirements, haircuts, liquidation thresholds, or credit eligibility.
- It does not recommend issuing, purchasing, selling, financing, or liquidating any token or asset.
- It is not financial, investment, accounting, tax, or legal advice.

## No oracle or production integration

- The JSON Schema is a draft data envelope, not a decentralized oracle.
- No signature verifier, issuer trust registry, or revocation service is implemented.
- No smart contract consumes or verifies the attestation.
- No production ledger, custody system, land registry, token registry, lender, or payment rail is integrated.
- No liveness, finality, reorganization, idempotency, or compensation guarantee has been demonstrated in code.

## No title, custody, or legal enforceability

- An `asset_id` does not prove legal title, custody, lien priority, encumbrance status, insurance coverage, or enforceability of token-holder rights.
- A cryptographic commitment proves only that some bytes were committed under the selected construction. It does not prove that the evidence is true, complete, recent, or lawfully collected.
- Issuer identity, professional authorization, revocation, and liability require governance and legal agreements outside this repository.

## Privacy is modeled, not implemented

- The repository recommends keeping raw property and occupant evidence private, but it does not implement encryption, selective-disclosure proofs, access control, key management, private information retrieval, or secure deletion.
- Hashes and pseudonymous identifiers can still leak metadata or enable correlation.
- Real property data and personal data must not be placed in public examples.

## Security and assurance

- The model has not undergone an independent security audit, legal review, accounting review, or professional valuation review.
- JSON Schema can check structural constraints but cannot establish cross-record authorization, temporal ordering, professional competence, or economic correctness.
- The state machine is a design aid and does not establish production safety.

## Relationship to other organizations

This is independent work by Miguel Herrero. It is not affiliated with, commissioned by, endorsed by, or presented on behalf of EthSystems, the Ethereum Foundation, a financial institution, a valuation firm, or a regulator.
