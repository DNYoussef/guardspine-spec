# GuardSpine Evidence Bundle Specification

> **Version**: 0.1.0
> **License**: Apache 2.0
> **Status**: Draft

The GuardSpine Evidence Bundle Specification defines a vendor-neutral, verifiable format for packaging governance evidence. Bundles can be verified offline by any party without trusting the issuing system.

## Why This Exists

In AI-mediated work governance, trust cannot depend on a single vendor. This specification enables:

- **Offline verification**: Auditors can verify bundles without network access
- **Vendor neutrality**: Any system can produce or consume compliant bundles
- **Cryptographic integrity**: Hash chains and signatures prove no tampering
- **Regulatory compliance**: Bundles meet evidentiary standards for SOX, HIPAA, SOC2

## Quick Start

```bash
# Install the verifier
pip install guardspine-verify

# Verify a bundle
guardspine-verify bundle.json

# Verify a ZIP export
guardspine-verify evidence-bundle-2024-01-15.zip
```

## Specification Documents

| Document | Description |
|----------|-------------|
| [SPECIFICATION.md](SPECIFICATION.md) | Full technical specification |
| [schemas/](schemas/) | JSON Schema definitions |
| [examples/](examples/) | Example bundles |

## Bundle Structure

A GuardSpine Evidence Bundle contains:

```
EvidenceBundle
+-- bundle_id          # Unique identifier (UUID)
+-- scope              # What is being asserted
|   +-- assertion_type
|   +-- assertion_text
|   +-- artifact_id
|   +-- version_from/to
|   +-- policy_ids[]
+-- items[]            # Evidence items
|   +-- item_id
|   +-- evidence_type  # diff | approval | policy_evaluation | ...
|   +-- content_hash   # SHA-256 of content
|   +-- content        # The actual evidence
+-- signatures[]       # Cryptographic signatures
|   +-- signer         # Human or AI identity
|   +-- algorithm      # ed25519 | rsa-sha256 | ecdsa-p256
|   +-- signature_value
|   +-- content_hash
+-- immutability_proof # Hash chain proving order
|   +-- root_hash      # Merkle root
|   +-- hash_chain     # Ordered chain of content hashes
+-- retention          # Retention policy
+-- audit_trail        # Who accessed/modified
```

## Verification Rules

A bundle is **VERIFIED** if and only if:

1. **Hash Chain Valid**: Each entry's `previous_hash` matches the prior entry's `content_hash`
2. **Root Hash Valid**: Computed Merkle root matches `immutability_proof.root_hash`
3. **Content Hashes Valid**: Each item's `content_hash` matches SHA-256 of its `content`
4. **Signatures Valid**: Each signature verifies against the signer's public key
5. **No Gaps**: Hash chain sequence numbers are contiguous starting from 0

## Supported Evidence Types

| Type | Description |
|------|-------------|
| `diff` | Deterministic diff between artifact versions |
| `approval` | Human or AI approval decision |
| `policy_evaluation` | Policy check results |
| `artifact_version` | Artifact snapshot metadata |
| `audit_event` | System event (view, export, etc.) |
| `signature` | Cryptographic signature event |

## Signature Algorithms

| Algorithm | Use Case |
|-----------|----------|
| `ed25519` | Default, fast, secure |
| `rsa-sha256` | Legacy system compatibility |
| `ecdsa-p256` | FIPS compliance |

## Retention Policies

| Policy | Retention | Use Case |
|--------|-----------|----------|
| `standard` | 1 year | Normal operations |
| `extended` | 3 years | Audit trail |
| `regulatory` | 7 years | SOX, HIPAA, GDPR |
| `permanent` | Forever | Legal hold |

## Export Formats

| Format | Description |
|--------|-------------|
| JSON | Machine-readable, single file |
| ZIP | Complete package with VERIFICATION.md |
| PDF | Human-readable report |
| SARIF | Security tool integration (SARIF 2.1.0) |

## Contributing

This specification is open for community input. To propose changes:

1. Open an issue describing the change
2. Submit a PR with spec updates + schema changes
3. Include test vectors for verification

## Implementations

| Implementation | Language | Status |
|----------------|----------|--------|
| [guardspine-verify](https://github.com/DNYoussef/guardspine-verify) | Python | Official |
| _Your implementation here_ | | |

## Important Disclaimers

**This specification provides evidence infrastructure, not compliance certification.**

- Bundles support audits; they don't replace auditor judgment
- Hash chains detect tampering; they don't prevent all attacks
- Control mappings are supportive metadata, not certification
- See [CLAIMS_GUARDRAIL.md](CLAIMS_GUARDRAIL.md) for detailed guidance

## License

Apache 2.0 - See [LICENSE](LICENSE)

---

**GuardSpine**: Evidence infrastructure for the AI office.
