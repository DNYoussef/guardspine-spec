# GuardSpine Evidence Bundle Specification v1.0.0

## 1. Introduction

### 1.1 Purpose

This specification defines the GuardSpine Evidence Bundle format, a standardized structure for packaging verifiable governance evidence. The format is designed to be:

- **Self-contained**: All evidence needed for verification is in the bundle
- **Verifiable offline**: No network access required to verify integrity
- **Vendor-neutral**: Any compliant system can produce or consume bundles
- **Cryptographically sound**: Uses established algorithms (SHA-256, Ed25519)

### 1.2 Version History

| Version | Date | Changes |
|---------|------|---------|
| v1.0.0 | 2026-01-20 | Added simplified event-based format, signature support |
| v0.1.0 | 2025-10-15 | Initial draft specification |

### 1.3 Terminology

| Term | Definition |
|------|------------|
| Bundle | A complete evidence package with scope, items, signatures, and proof |
| Evidence Item | A single piece of evidence (diff, approval, etc.) |
| Event | A timestamped action in the audit trail (v1.0+ format) |
| Hash Chain | Ordered sequence of content hashes proving temporal order |
| Signer | Human or AI entity that cryptographically signs the bundle |
| Scope | What the bundle asserts about an artifact |

### 1.4 Conformance

An implementation is conformant if it:
- Produces bundles that pass verification according to Section 5
- Consumes bundles without rejecting valid ones
- Reports verification failures according to Section 6

---

## 2. Bundle Structure

### 2.1 Top-Level Schema

```json
{
  "bundle_id": "uuid",
  "bead_id": "string",
  "artifact_id": "string",
  "from_version_id": "string",
  "to_version_id": "string",
  "risk_tier": "L0" | "L1" | "L2" | "L3" | "L4",
  "scope": { ... },
  "items": [ ... ],
  "signatures": [ ... ],
  "immutability_proof": { ... },
  "retention": { ... },
  "export_status": "pending" | "exported" | "failed",
  "integrity_status": "verified" | "unverified" | "mismatch",
  "created_at": "ISO8601",
  "updated_at": "ISO8601",
  "verified_at": "ISO8601 | null",
  "exported_at": "ISO8601 | null",
  "audit_trail": { ... }
}
```

### 2.2 Evidence Scope

The scope defines what is being asserted:

```json
{
  "assertion_type": "change_approval" | "policy_compliance" | "audit_evidence",
  "assertion_text": "string (human-readable assertion)",
  "artifact_id": "string",
  "version_from": "string",
  "version_to": "string",
  "policy_ids": ["string"],
  "risk_tier_assessed": "L0" | "L1" | "L2" | "L3" | "L4",
  "assessment_date": "ISO8601"
}
```

### 2.3 Evidence Items

Each item contains a piece of evidence:

```json
{
  "item_id": "uuid",
  "evidence_type": "diff" | "approval" | "policy_evaluation" | "artifact_version" | "audit_event" | "signature",
  "content_hash": "sha256:hex",
  "content": { ... },
  "created_at": "ISO8601"
}
```

**Evidence Type Schemas:**

#### 2.3.1 Diff Evidence

```json
{
  "evidence_type": "diff",
  "content": {
    "diff_id": "string",
    "algorithm": "myers" | "patience" | "histogram",
    "from_hash": "sha256:hex",
    "to_hash": "sha256:hex",
    "hunks": [
      {
        "old_start": "int",
        "old_count": "int",
        "new_start": "int",
        "new_count": "int",
        "lines": [
          { "type": "context" | "add" | "remove", "content": "string" }
        ]
      }
    ],
    "stats": {
      "additions": "int",
      "deletions": "int",
      "changes": "int"
    }
  }
}
```

#### 2.3.2 Approval Evidence

```json
{
  "evidence_type": "approval",
  "content": {
    "approval_id": "string",
    "approver": { ... },  // SignerIdentity
    "decision": "approved" | "rejected" | "deferred",
    "rationale": "string",
    "conditions": ["string"],
    "decided_at": "ISO8601"
  }
}
```

#### 2.3.3 Policy Evaluation Evidence

```json
{
  "evidence_type": "policy_evaluation",
  "content": {
    "evaluation_id": "string",
    "policy_id": "string",
    "policy_version": "string",
    "result": "pass" | "fail" | "warn",
    "findings": [
      {
        "finding_id": "string",
        "severity": "critical" | "high" | "medium" | "low" | "info",
        "message": "string",
        "location": "string | null"
      }
    ],
    "evaluated_at": "ISO8601"
  }
}
```

### 2.4 Signer Identity

```json
{
  "signer_id": "string",
  "signer_type": "human" | "ai_model" | "system",
  "display_name": "string",
  "email": "string | null",
  "ai_model_id": "string | null",
  "ai_model_version": "string | null",
  "public_key_id": "string | null",
  "organization": "string | null"
}
```

### 2.5 Signature

```json
{
  "signature_id": "uuid",
  "algorithm": "ed25519" | "rsa-sha256" | "ecdsa-p256",
  "signer": { ... },  // SignerIdentity
  "signature_value": "base64",
  "signed_at": "ISO8601",
  "content_hash": "sha256:hex",
  "certificate_chain": ["base64"] | null
}
```

### 2.6 Immutability Proof

```json
{
  "proof_id": "uuid",
  "bundle_id": "string",
  "root_hash": "sha256:hex",
  "hash_algorithm": "sha256",
  "hash_chain": {
    "chain_id": "uuid",
    "entries": [
      {
        "sequence_number": "int",
        "content_hash": "sha256:hex",
        "previous_hash": "sha256:hex | null",
        "timestamp": "ISO8601",
        "content_type": "string",
        "content_id": "string"
      }
    ],
    "created_at": "ISO8601"
  },
  "verified_at": "ISO8601 | null",
  "verification_status": "verified" | "unverified" | "mismatch"
}
```

### 2.7 Retention Configuration

```json
{
  "policy": "standard" | "extended" | "regulatory" | "permanent",
  "retention_days": "int",
  "created_at": "ISO8601",
  "expires_at": "ISO8601",
  "legal_hold": "boolean",
  "compliance_frameworks": ["string"]
}
```

### 2.8 Audit Trail

```json
{
  "bundle_id": "string",
  "entries": [
    {
      "entry_id": "uuid",
      "bundle_id": "string",
      "action": "created" | "viewed" | "verified" | "exported" | "signed" | "modified" | "deleted",
      "actor": { ... },  // SignerIdentity
      "timestamp": "ISO8601",
      "details": { ... },
      "ip_address": "string | null",
      "user_agent": "string | null"
    }
  ],
  "last_modified": "ISO8601"
}
```

### 2.9 Event-Based Format (v1.0+)

The v1.0+ format introduces a simplified event-based structure suitable for CI/CD pipelines and code review workflows:

```json
{
  "guardspine_spec_version": "1.0.0",
  "bundle_id": "gsb_xxxxxxxxxxxx",
  "created_at": "ISO8601",
  "context": {
    "repository": "owner/repo",
    "pr_number": 123,
    "commit_sha": "string",
    "base_branch": "main",
    "head_branch": "feature-branch"
  },
  "events": [
    {
      "event_type": "audit_started" | "analysis_completed" | "risk_classified" | "approval_granted",
      "timestamp": "ISO8601",
      "actor": "string",
      "data": { ... },
      "hash": "sha256_hex"
    }
  ],
  "hash_chain": {
    "algorithm": "sha256",
    "final_hash": "sha256_hex",
    "event_count": "int"
  },
  "summary": {
    "risk_tier": "L0" | "L1" | "L2" | "L3" | "L4",
    "findings": [ ... ],
    "rationale": "string"
  },
  "provenance": {
    "tool": { "name": "string", "version": "string" },
    "models": { "backend": "string", "used": ["string"] }
  },
  "signatures": [
    {
      "type": "ed25519" | "rsa-sha256" | "ecdsa-sha256" | "hmac-sha256",
      "signer": "string",
      "timestamp": "ISO8601",
      "signature": "base64",
      "public_key_fingerprint": "sha256_hex"
    }
  ]
}
```

#### 2.9.1 Event Types

| Type | Description |
|------|-------------|
| `audit_started` | Audit process initiated |
| `analysis_completed` | Model analysis finished |
| `risk_classified` | Risk tier assigned |
| `approval_granted` | Human approval recorded (L4) |

#### 2.9.2 Event Hash Chain

Each event's hash includes the previous event's hash, creating a tamper-evident chain:

```
event[n].hash = SHA256(canonical_json({
  "event_type": event[n].event_type,
  "timestamp": event[n].timestamp,
  "actor": event[n].actor,
  "data": event[n].data,
  "previous_hash": event[n-1].hash  // empty string for first event
}))
```

---

## 3. Hash Chain Construction

### 3.1 Algorithm

1. For each evidence item added to the bundle:
   a. Compute `content_hash = SHA256(canonical_json(content))`
   b. Create chain entry with `sequence_number = len(chain)`
   c. Set `previous_hash = chain[-1].content_hash` (or null if first)
   d. Append entry to chain

2. Compute root hash:
   ```
   root_hash = SHA256(concat(entry[0].content_hash, entry[1].content_hash, ...))
   ```

### 3.2 Canonical JSON

Content MUST be serialized using canonical JSON (RFC 8785):
- Keys sorted alphabetically
- No whitespace
- UTF-8 encoding
- Numbers as integers or decimals (no scientific notation)

---

## 4. Signature Algorithm

### 4.1 Signing Process

1. Compute `content_to_sign = SHA256(canonical_json(bundle_without_signatures))`
2. Sign using the signer's private key
3. Encode signature as base64
4. Add signature object to `signatures[]`

### 4.2 Algorithm-Specific Details

**Ed25519:**
- Key size: 256 bits
- Signature size: 512 bits (64 bytes)

**RSA-SHA256:**
- Minimum key size: 2048 bits
- Padding: PKCS#1 v1.5

**ECDSA-P256:**
- Curve: NIST P-256
- Hash: SHA-256

---

## 5. Verification Rules

A bundle is **VERIFIED** if ALL of the following pass:

### 5.1 Hash Chain Verification

```
FOR each entry in hash_chain.entries[1..]:
  ASSERT entry.previous_hash == entries[entry.sequence_number - 1].content_hash
```

### 5.2 Root Hash Verification

```
computed_root = SHA256(concat(all content_hashes in order))
ASSERT computed_root == immutability_proof.root_hash
```

### 5.3 Content Hash Verification

```
FOR each item in items:
  computed_hash = SHA256(canonical_json(item.content))
  ASSERT computed_hash == item.content_hash
```

### 5.4 Signature Verification

```
FOR each signature in signatures:
  content_to_verify = SHA256(canonical_json(bundle_without_signatures))
  ASSERT verify(signature.algorithm, signature.signer.public_key, content_to_verify, signature.signature_value)
```

### 5.5 Sequence Continuity

```
FOR i in range(len(hash_chain.entries)):
  ASSERT hash_chain.entries[i].sequence_number == i
```

---

## 6. Error Reporting

Verification failures MUST report:

| Error Code | Description |
|------------|-------------|
| `HASH_CHAIN_BROKEN` | Previous hash mismatch |
| `ROOT_HASH_MISMATCH` | Computed root != stored root |
| `CONTENT_HASH_MISMATCH` | Item content hash invalid |
| `SIGNATURE_INVALID` | Signature verification failed |
| `SEQUENCE_GAP` | Non-contiguous sequence numbers |
| `MISSING_REQUIRED_FIELD` | Required field is null/missing |

---

## 7. Export Formats

### 7.1 JSON Export

Single file containing the complete bundle as JSON.

### 7.2 ZIP Export

```
bundle-{id}.zip
+-- bundle.json           # Complete bundle
+-- VERIFICATION.md       # Human-readable verification instructions
+-- signatures/           # Detached signature files
|   +-- sig-{id}.sig
+-- attachments/          # Original artifacts (optional)
```

### 7.3 PDF Export

Human-readable report with:
- Executive summary
- Evidence items
- Verification status
- Signature attestations

### 7.4 SARIF Export

SARIF 2.1.0 format for security tool integration.

---

## 8. Security Considerations

### 8.1 Key Management

- Private keys MUST be stored securely (HSM recommended for production)
- Key rotation SHOULD occur at least annually
- Compromised keys MUST be revoked immediately

### 8.2 Hash Algorithm Agility

- SHA-256 is the current default
- Implementations SHOULD support algorithm migration
- Hash algorithm MUST be stored in `immutability_proof.hash_algorithm`

### 8.3 Timestamp Integrity

- Timestamps SHOULD use a trusted time source
- For high-assurance use cases, consider timestamping authorities (RFC 3161)

---

## Appendix A: JSON Schema

See `schemas/` directory for complete JSON Schema definitions.

## Appendix B: Test Vectors

See `test-vectors/` directory for verification test cases.

## Appendix C: Reference Implementation

See [guardspine-verify](https://github.com/guardspine/guardspine-verify) for the official Python implementation.
