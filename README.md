# GuardSpine Evidence Bundle Specification

> **Version**: 0.2.1
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

A GuardSpine Evidence Bundle (v0.2.x) contains:

```
EvidenceBundle
+-- bundle_id          # Unique identifier (UUID)
+-- version            # "0.2.0" | "0.2.1"
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
+-- sanitization       # Optional redaction/sanitization attestation (v0.2.1+)
|   +-- engine_name
|   +-- engine_version
|   +-- method
|   +-- token_format   # [HIDDEN:<id>]
|   +-- redaction_count
+-- audit_trail        # Who accessed/modified
```

## Verification Rules

A bundle is **VERIFIED** if and only if:

1. **Version Valid**: Bundle `version` field equals `"0.2.0"` or `"0.2.1"`
2. **Hash Chain Valid**: Each entry's `previous_hash` matches the prior entry's `chain_hash` (NOT content_hash)
3. **Chain Binding**: Hash chain entries map 1:1 to items (same count, same item_id, same content_hash, same order)
4. **Root Hash Valid**: Computed Merkle root matches `immutability_proof.root_hash`
5. **Content Hashes Valid**: Each item's `content_hash` matches SHA-256 of its canonical JSON `content`
6. **Signatures Valid**: Each signature verifies against the signer's public key
7. **No Gaps**: Hash chain sequence numbers are contiguous starting from 0
8. **Sanitization Contract (Optional)**: If `sanitization` is present, it matches schema rules (v0.2.1+)

**Important**: The chain links via `chain_hash`, not `content_hash`. This is a common implementation error.

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

## Sanitization Attestation (v0.2.1)

Bundles may optionally include:

- `sanitization.engine_name` / `engine_version`
- `sanitization.method` (`deterministic_hmac`, `provider_native`, `entropy+hmac`)
- `sanitization.token_format` (`[HIDDEN:<id>]`)
- `sanitization.redaction_count` and `redactions_by_type`
- `sanitization.status` (`sanitized`, `none`, `partial`, `error`)

This field documents redaction behavior for downstream policy checks.

### PII-Shield Integration

The sanitization attestation schema was designed in collaboration with [PII-Shield](https://github.com/aragossa/pii-shield), a Go-based Kubernetes sidecar that detects secrets via Shannon entropy analysis and replaces them with deterministic HMAC tokens.

**Why**: Evidence bundles may contain secrets or PII from code diffs, approval messages, or integration payloads. The sanitization attestation block provides a standardized way for any implementation to document what was redacted, how, and by which engine -- enabling downstream verifiers to validate the sanitization contract.

**Where**: The `sanitization` schema is defined in:
- `schemas/evidence-bundle.schema.json` (v0.2.0 base)
- `schemas/evidence-bundle-v0.2.1.schema.json` (v0.2.1 with full sanitization support)

**How implementations use it**: Any bundle producer (codeguard-action, rlm-docsync, adapter-webhook, local-council) that sanitizes content before sealing populates the `sanitization` block. The verifier (guardspine-verify) checks that `redaction_count` matches actual token count and that `engine_version` is valid semver.

### Cryptographic Field Registry

The spec defines a **crypto field registry** that identifies which JSON fields contain intentionally high-entropy values (hashes, signatures) vs. fields that might contain accidental secrets. This matters because PII-Shield's entropy detector will flag SHA-256 hashes as secrets without it.

Reserved field patterns: `*_hash`, `*_digest`, `*_checksum`, `*_hmac`, `*_signature`, `signature_value`, `signed_hash`.

### PII_SALT Requirements

The HMAC salt used for deterministic redaction (`[HIDDEN:<id>]` tokens) **must be org-wide and immutable**. If different services use different salts, the same secret produces different tokens across bundles, breaking cross-bundle correlation and audit trail consistency. See `SPECIFICATION.md` for the full contract.

### Z-Inspection Integration

The spec includes a guide for integrating GuardSpine evidence bundles with the [Z-Inspection](https://z-inspection.org/) process for trustworthy AI assessment. Evidence bundles provide the artifact trail that Z-Inspection panels need for socio-technical evaluation. See `docs/z-inspection-guide.md`.

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
| `v0.2.1-sanitized-bundle.json` | Bundle with sanitization attestation |
| `malformed/*.json` | Invalid bundles that MUST be rejected |

The `examples/` directory contains illustrative examples:

| Example | Description | Status |
|---------|-------------|--------|
| `code-diff-bundle.json` | Code change review evidence | Legacy format (v0.1.0) |
| `pdf-diff-bundle.json` | PDF document change evidence | Legacy format (v0.1.0) |
| `xlsx-diff-bundle.json` | Excel document change evidence | Legacy format (v0.1.0) |

**Note**: Examples in `examples/` use legacy field names (`evidence_type` instead of `content_type`).
For v0.2.0 compliant examples, see `fixtures/golden-vectors/`.

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
