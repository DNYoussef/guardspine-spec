# External Claims Guardrail

**Purpose:** Prevent overclaiming while describing GuardSpine capabilities accurately.

## What GuardSpine IS

- **Evidence infrastructure** for tracking changes, approvals, and policy evaluations
- **Cryptographically verifiable** bundles that can be validated offline
- **Vendor-neutral format** that works without GuardSpine systems
- **Audit trail generator** that creates defensible records of decisions

## What GuardSpine is NOT

- **Not a compliance certification** - bundles support audits, they don't replace them
- **Not a legal guarantee** - evidence quality depends on your implementation
- **Not tamper-proof storage** - we prove integrity, not prevent all attacks
- **Not a replacement for security controls** - we document, not enforce

## Claim Guidelines

### SAFE to claim:

- "Bundles can be verified offline without trusting GuardSpine"
- "Hash chains prove the sequence of events was not modified"
- "Evidence bundles include who approved, what changed, and when"
- "The spec is open and vendor-neutral"
- "Auditors can independently verify bundle integrity"

### AVOID claiming:

- "GuardSpine makes you SOC 2 compliant" → Instead: "GuardSpine generates evidence that supports SOC 2 audits"
- "Bundles are tamper-proof" → Instead: "Bundles detect tampering through hash chain verification"
- "This proves legal compliance" → Instead: "This provides auditable evidence of decisions"
- "AI decisions are governed" → Instead: "AI-assisted changes are tracked with human approval records"

## Technical Limitations to Disclose

### Canonicalization
- JSON ordering and whitespace can affect hashes across implementations
- Timestamps should use ISO 8601 with UTC timezone
- Floating point numbers may have precision issues

### Key Management
- Long-term signature validity depends on key rotation practices
- "AI signer" keys require clear custody and audit procedures
- Key compromise invalidates signatures made with that key

### Scale
- Bundle verification is O(n) with chain length
- Very large bundles (>10MB) may have performance implications
- High-volume systems need archival strategy

### Signatures
- Signature verification requires access to public keys
- Key distribution is outside the spec scope
- Certificate/key expiry checking is implementation-dependent

## When Talking to Auditors

**Say:** "These bundles provide a cryptographically linked record of changes and approvals. You can verify the integrity yourself with our open-source CLI tool."

**Don't say:** "This guarantees compliance" or "This is legally binding evidence."

## When Talking to Security Teams

**Say:** "Hash chains detect modification. If someone alters a bundle, verification will fail."

**Don't say:** "This is unhackable" or "Bundles can't be forged."

---

*This document should be referenced before any external communication about GuardSpine capabilities.*
