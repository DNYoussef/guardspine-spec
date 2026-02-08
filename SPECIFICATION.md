# GuardSpine Evidence Bundle Specification v0.2.0

## 1. Introduction

### 1.1 Purpose

This specification defines the canonical GuardSpine Evidence Bundle format used
across the ecosystem for offline, tamper-evident verification.

Design goals:
- **Self-contained** evidence bundles
- **Offline verification** without network access
- **Deterministic hashing** across implementations
- **Interoperable** across GuardSpine repositories

### 1.2 Version History

| Version | Date | Changes |
|---------|------|---------|
| v0.2.1 | 2026-02-08 | Added optional `sanitization` attestation object |
| v0.2.0 | 2026-02-02 | Canonical bundle schema aligned with kernel v0.2.0 |
| v1.0.0 | 2026-01-20 | **Deprecated** draft (replaced by v0.2.0) |
| v0.1.0 | 2025-10-15 | Initial draft |

### 1.3 Conformance

An implementation is conformant if it:
- Emits bundles that validate against `schemas/evidence-bundle.schema.json` (v0.2.0)
  or `schemas/evidence-bundle-v0.2.1.schema.json` (v0.2.1)
- Computes content hashes and hash chains exactly as defined in Section 4
- Verifies bundles using the algorithm in Section 5

---

## 2. Bundle Structure (v0.2.0)

### 2.1 Top-Level Schema

```json
{
  "bundle_id": "uuid",
  "version": "0.2.0",
  "created_at": "ISO8601",
  "policy_id": "string?",
  "artifact_id": "string?",
  "risk_tier": "L0|L1|L2|L3|L4?",
  "sanitization": { ... }?,
  "items": [ ... ],
  "immutability_proof": { ... },
  "signatures": [ ... ],
  "metadata": { ... }
}
```

Required fields: `bundle_id`, `version`, `created_at`, `items`, `immutability_proof`.

### 2.2 Evidence Items

Each item is a structured piece of evidence. The `content_hash` **MUST** be the
SHA-256 of the canonical JSON serialization of `content`.

```json
{
  "item_id": "string",
  "content_type": "guardspine/diff | guardspine/approval | ...",
  "content": { ... },
  "content_hash": "sha256:hex",
  "sequence": 0
}
```

### 2.3 Immutability Proof

`immutability_proof` binds item order and metadata into a hash chain.
Each `HashChainLink` includes `sequence`, `item_id`, `content_type`, and
`content_hash` to prevent substitution attacks.

```json
{
  "hash_chain": [
    {
      "sequence": 0,
      "item_id": "...",
      "content_type": "guardspine/...",
      "content_hash": "sha256:...",
      "previous_hash": "genesis",
      "chain_hash": "sha256:..."
    }
  ],
  "root_hash": "sha256:..."
}
```

### 2.4 Signatures (Optional)

Signatures are optional. When present, they MUST sign the bundle with the
`signatures` array removed.

```json
{
  "signature_id": "uuid",
  "algorithm": "ed25519 | rsa-sha256 | ecdsa-p256 | hmac-sha256",
  "signer_id": "string",
  "signature_value": "base64",
  "signed_at": "ISO8601",
  "public_key_id": "string?"
}
```

### 2.5 Sanitization Attestation (Optional, v0.2.1+)

When sensitive content has been redacted before or during evidence generation,
producers SHOULD include a `sanitization` object:

```json
{
  "engine_name": "pii-shield",
  "engine_version": "1.1.0",
  "method": "deterministic_hmac",
  "token_format": "[HIDDEN:<id>]",
  "salt_fingerprint": "sha256:1a2b3c4d",
  "redaction_count": 3,
  "redactions_by_type": { "email": 1, "api_key": 2 },
  "input_hash": "sha256:...",
  "output_hash": "sha256:...",
  "applied_to": ["ai_prompt", "evidence_bundle", "sarif"],
  "status": "sanitized"
}
```

`sanitization` is informational attestation metadata and is not itself a cryptographic proof
of redaction completeness. Consumers MAY apply additional policy checks.

The `input_hash` field MUST contain the SHA-256 hash of the content before
sanitization was applied. The `output_hash` field MUST contain the SHA-256
hash of the content after sanitization. When `applied_to` includes
"evidence_bundle", the `output_hash` covers the serialized bundle content
(excluding the `sanitization` block itself) after all redactions.
Individual `content_hash` values on items reflect their post-sanitization
content. The relationship is: items are sanitized first, then their
content_hash values are computed over the sanitized content, then the
hash chain and root_hash are built.

---

## 3. Canonical JSON (RFC 8785 Compatible)

Canonical JSON rules:
- Object keys sorted lexicographically
- No extra whitespace
- Strings escaped as in JSON
- Numbers serialized using shortest round-trip representation

**Note**: All numeric values should remain within the JSON/IEEE-754 safe range
for deterministic cross-language serialization.

---

## 4. Hashing Rules

### 4.1 Content Hash

```
content_hash = SHA256(canonical_json(content))
```

### 4.2 Chain Hash

```
chain_hash = SHA256("sequence|item_id|content_type|content_hash|previous_hash")
```

`previous_hash` is the prior `chain_hash`, or the literal string `genesis`
for the first link.

### 4.3 Root Hash

```
root_hash = SHA256(concat(chain_hash[0], chain_hash[1], ...))
```

---

## 5. Verification Algorithm

1. Validate required fields and schema conformance.
2. Recompute each `content_hash` and compare.
3. Recompute each `chain_hash` and validate `previous_hash` linkage.
4. Recompute `root_hash` from all chain hashes and compare.
5. If signatures present, verify against bundle content without `signatures`.
6. If `sanitization` is present:
   a. Validate the `sanitization` object against the SanitizationSummary
      schema (all required fields present and correctly typed).
   b. Verify `token_format` matches the canonical pattern `[HIDDEN:<id>]`.
   c. If `redaction_count` > 0, scan item content strings for tokens
      matching `[HIDDEN:<identifier>]` and verify the count matches
      `redaction_count`.
   d. If `output_hash` is present, verify it matches the SHA-256 hash
      of the sanitized content.
   e. Verify `sum(redactions_by_type.values()) == redaction_count`.

If any step fails, the bundle is invalid.

---

## 6. Backward Compatibility

- v1.0.0 draft bundles are deprecated.
- Implementations MAY provide migration tools, but v0.2.0 is the canonical format.
