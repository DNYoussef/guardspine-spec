# GuardSpine Evidence Bundle Specification

> **Version**: 0.2.0
> **License**: Apache 2.0
> **Status**: Stable

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

The GuardSpine Evidence Bundle Specification defines a vendor-neutral, verifiable format for packaging governance evidence. Bundles can be verified offline by any party without trusting the issuing system.

## Why This Exists

In AI-mediated work governance, trust cannot depend on a single vendor. This specification enables:

- **Offline verification**: Auditors can verify bundles without network access
- **Vendor neutrality**: Any system can produce or consume compliant bundles
- **Cryptographic integrity**: Hash chains and signatures prove no tampering
- **Regulatory compliance**: Bundles meet evidentiary standards for SOX, HIPAA, SOC2

## Quick Start

```bash
# Clone and install dependencies
git clone https://github.com/DNYoussef/guardspine-spec.git
cd guardspine-spec
npm install

# Validate bundles against schema
npm run validate

# Run interoperability tests
pip install pytest jsonschema
pytest tests/ -v
```

### Using the Verifier

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
| [CLAIMS_GUARDRAIL.md](CLAIMS_GUARDRAIL.md) | Important disclaimers |
| [schemas/](schemas/) | JSON Schema definitions |
| [examples/](examples/) | Example bundles |

## Bundle Structure

A GuardSpine Evidence Bundle (v0.2.0) contains:

```
EvidenceBundle
+-- bundle_id          # Unique identifier (UUID)
+-- version            # "0.2.0"
+-- created_at         # ISO 8601 timestamp
+-- items[]            # Evidence items
|   +-- item_id
|   +-- content_type   # guardspine/* type tag
|   +-- content_hash   # SHA-256 of canonical JSON content
|   +-- content        # The actual evidence
|   +-- sequence       # 0-based index
+-- immutability_proof # Hash chain + root hash
|   +-- hash_chain[]
|   |   +-- sequence
|   |   +-- item_id
|   |   +-- content_type
|   |   +-- content_hash
|   |   +-- previous_hash
|   |   +-- chain_hash
|   +-- root_hash
+-- signatures[]       # Optional cryptographic signatures
|   +-- signature_id   # Unique signature ID
|   +-- signer_id      # Human or AI identity ID
|   +-- algorithm      # ed25519 | rsa-sha256 | ecdsa-p256
|   +-- signature_value
|   +-- signed_at      # ISO 8601 timestamp
|   +-- content_hash
+-- metadata           # Bundle metadata
|   +-- retention      # Retention policy
+-- audit_trail        # Who accessed/modified
```

## Verification Rules

A bundle is **VERIFIED** if and only if:

1. **Hash Chain Valid**: Each entry's `previous_hash` matches the prior entry's `chain_hash`
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
| `integration_event` | External system event (GitHub, Jira, Slack) |
| `dlp_signal` | DLP/CASB classification signal |

## Signature Algorithms

| Algorithm | Use Case |
|-----------|----------|
| `ed25519` | Default, fast, secure |
| `rsa-sha256` | Legacy system compatibility |
| `ecdsa-p256` | FIPS compliance |

## AI Signer Identity

For AI-generated evidence, signers include model provenance:

```json
{
  "signer_type": "ai_model",
  "signer_id": "claude-3-opus-20240229",
  "display_name": "Claude 3 Opus",
  "ai_model_id": "claude-3-opus-20240229",
  "ai_model_version": "20240229",
  "organization": "Anthropic"
}
```

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

## Integration with External Systems

Bundles can include evidence from:

- **GitHub**: Push events, PR reviews, code scanning alerts
- **Jira**: Issue links, status changes
- **Slack**: Approval decisions, rejection rationale
- **Microsoft 365**: Document changes, sensitivity labels
- **DLP/CASB**: Classification signals, policy violations

## Contributing

This specification is open for community input. To propose changes:

1. Open an issue describing the change
2. Submit a PR with spec updates + schema changes
3. Include test vectors for verification

## Test Fixtures

The `fixtures/golden-vectors/` directory contains:

| Vector | Description |
|--------|-------------|
| `v0.2.0-minimal-bundle.json` | Smallest valid bundle (1 item) |
| `v0.2.0-multi-item-bundle.json` | Bundle with 5 items |
| `v0.2.0-signed-bundle.json` | Bundle with Ed25519 signature |
| `malformed/*.json` | Invalid bundles that MUST be rejected |

The `examples/` directory contains real-world examples:

| Example | Description |
|---------|-------------|
| `code-diff-bundle.json` | Code change review evidence |
| `pdf-diff-bundle.json` | PDF document change evidence |
| `xlsx-diff-bundle.json` | Excel document change evidence |

## Validation Tools

```bash
# Run schema validation on all fixtures and examples
npm run validate

# Output shows: valid bundles, expected failures, any errors
```

The validation script uses AJV with JSON Schema 2020-12 support.

## Implementations

| Implementation | Language | Status |
|----------------|----------|--------|
| [@guardspine/kernel](https://github.com/DNYoussef/guardspine-kernel) | TypeScript | Core library |
| [guardspine-kernel-py](https://github.com/DNYoussef/guardspine-kernel-py) | Python | Python bridge |
| [guardspine-verify](https://github.com/DNYoussef/guardspine-verify) | Python | Verifier CLI |
| [guardspine-product](https://github.com/DNYoussef/guardspine-product) | Python | Evidence producers |
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
