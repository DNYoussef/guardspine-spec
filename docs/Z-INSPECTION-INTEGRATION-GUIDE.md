# Z-Inspection x GuardSpine Integration Guide

**Version**: 0.1.0-draft
**Date**: 2026-02-09
**Authors**: David Youssef, [Ishwar Chavhan - invited contributor]
**Status**: Research draft - pending Z-Inspection advisor review

---

## Executive Summary

Z-Inspection is a 9-step, 3-phase process for assessing trustworthy AI, developed under the EU High-Level Expert Group framework. It maps findings to the 7 ALTAI requirements. GuardSpine generates cryptographically sealed evidence bundles for AI-mediated code changes. The integration thesis: GuardSpine can automate evidence generation for 4 of the 7 ALTAI requirements, converting Z-Inspection from point-in-time manual audits to continuous machine-verifiable evidence trails.

---

## Part 1: Z-Inspection Process Overview

### The 3 Phases, 9 Steps

```
PHASE 1: SET UP
  Step 1: Pre-conditions verification (legal admissibility, conflict of interest)
  Step 2: Team formation (multidisciplinary experts)
  Step 3: Protocol documentation (log of inspection process over time)
  Step 4: Boundary definition (scope of assessment)

PHASE 2: ASSESS
  Step 5: Socio-technical scenario analysis (actors, expectations, processes, tech, context)
  Step 6: Ethical issue identification (consensus building among stakeholders)
  Step 7: Trustworthy AI mapping (map issues to EU 7 ALTAI requirements)

PHASE 3: RESOLVE
  Step 8: Execution (define paths, perform inspection, provide feedback)
  Step 9: Resolution & maintenance (address tensions, recommend, ethical maintenance)
```

Source: Z-Inspection process (z-inspection.org), IEEE publication (Zicari et al., 2021)

### The 7 ALTAI Requirements

| # | Requirement | Sub-categories |
|---|-------------|----------------|
| 1 | Human Agency & Oversight | Fundamental rights, human agency, human oversight |
| 2 | Technical Robustness & Safety | Resilience/security, fallback/safety, accuracy, reliability/reproducibility |
| 3 | Privacy & Data Governance | Privacy respect, data quality/integrity, data access |
| 4 | Transparency | Traceability, explainability, communication |
| 5 | Diversity, Non-discrimination & Fairness | Unfair bias avoidance, accessibility, universal design |
| 6 | Societal & Environmental Well-being | Sustainability, social impact, society/democracy |
| 7 | Accountability | Auditability, negative impact minimization/reporting, trade-offs, redress |

Source: EU HLEG "Ethics Guidelines for Trustworthy AI" (2019), ALTAI self-assessment checklist (2020)

### Current Pain Points in Z-Inspection

1. **Manual evidence gathering**: Assessors collect screenshots, meeting notes, spreadsheets
2. **Point-in-time snapshots**: Assessment happens once, not continuously
3. **No tamper evidence**: Documents can be modified after assessment
4. **Mapping is subjective**: Mapping issues to ALTAI requirements is consensus-based, not machine-verifiable
5. **No retention infrastructure**: Assessment artifacts scattered across tools

---

## Part 2: GuardSpine Evidence Bundle Schema (v0.2.1)

### Top-Level Structure

```json
{
  "bundle_id": "UUID v4",
  "version": "0.2.1",
  "created_at": "ISO 8601 timestamp",
  "policy_id": "reference to rubric used",
  "artifact_id": "what was assessed (e.g., github:org/repo/file)",
  "risk_tier": "L0|L1|L2|L3|L4",
  "items": [ "ordered evidence items" ],
  "immutability_proof": { "hash_chain": [], "root_hash": "sha256:..." },
  "signatures": [ "cryptographic signatures" ],
  "sanitization": { "PII-Shield attestation" },
  "metadata": { "extensible key-value" }
}
```

### Evidence Item Types

| content_type | Purpose | Fields |
|-------------|---------|--------|
| `diff` | Code change snapshot | hunks, line-level changes, from/to hashes, stats |
| `policy_evaluation` | Policy check results | policy_id, policy_version, result (pass/fail), findings[] |
| `approval` | Human/AI decision record | approver (id, type, name, org), decision, rationale, conditions |
| `guardspine/audit_event` | System-level event | event_type, message, details |
| `guardspine/test-result` | Test execution evidence | test results, pass/fail |

### Immutability Proof

Each item gets a hash chain link: `chain_hash = SHA-256(sequence | item_id | content_type | content_hash | previous_hash)`. The root_hash covers all chain_hash values. Any modification to any item invalidates the chain.

### Signature Support

Algorithms: Ed25519, RSA-SHA256, ECDSA-P256, HMAC-SHA256. Each signature records: signer_id, signer_type (human/ai_model/system), signed_at timestamp, public_key_id reference.

### Sanitization Attestation (v0.2.1)

PII-Shield integration records: engine, method (deterministic_hmac), redaction counts by type, input/output hashes, which pipeline stages were sanitized.

---

## Part 3: Requirement-Level Mapping

### Mapping Legend

| Coverage | Meaning |
|----------|---------|
| STRONG | Direct evidence bundle fields address this requirement |
| MODERATE | Partial coverage; bundle fields contribute but don't fully satisfy |
| WEAK | Tangential connection; not a primary design goal |
| GAP | No current coverage; integration opportunity |

---

### Requirement 4: Transparency (STRONG)

This is GuardSpine's primary strength relative to Z-Inspection.

#### 4.1 Traceability

ALTAI asks: Can the decisions and actions of the AI system be traced back? Are the datasets, processes, and decisions documented?

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Can AI decisions be traced? | Every event in the PR lifecycle is recorded with timestamps | `items[].created_at`, `items[].sequence` |
| Are datasets documented? | The exact diff (code change) is captured at analysis time | `items[content_type=diff].content.hunks` |
| Are processes documented? | Hash chain proves the order and integrity of all steps | `immutability_proof.hash_chain[]` |
| Is there a decision log? | Full audit trail with actor identity and action type | `audit_trail.entries[]` |
| Can outcomes be reproduced? | Content hashes are deterministic (same input = same hash) | `items[].content_hash` |

#### 4.2 Explainability

ALTAI asks: Can the AI system's decisions be explained? Is the logic transparent?

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Why was this risk tier assigned? | Policy evaluation findings explain classification | `items[content_type=policy_evaluation].content.findings[]` |
| What assertion is being made? | Scope block contains the assertion text | `scope.assertion_text` |
| Why was this approved/rejected? | Approver records include written rationale | `items[content_type=approval].content.rationale` |
| What conditions were set? | Conditional approvals are recorded | `items[content_type=approval].content.conditions[]` |

#### 4.3 Communication

ALTAI asks: Are users informed about the AI system's capabilities and limitations?

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Are stakeholders informed of AI involvement? | Diff Postcard PR comment shows risk tier + AI findings | CodeGuard PR comment output |
| Are findings accessible? | SARIF export feeds GitHub Security Tab | `upload_sarif` output |
| Are limitations communicated? | Multi-model agreement score shows confidence level | `agreement_score`, `dissenting_opinions` |

---

### Requirement 7: Accountability (STRONG)

#### 7.1 Auditability

ALTAI asks: Can the AI system be audited by independent third parties? Are there mechanisms for logging?

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Can independent third parties audit? | Bundle is a standalone JSON file; guardspine-verify works offline with zero vendor dependency | `immutability_proof.root_hash` + guardspine-verify CLI |
| Are there logging mechanisms? | Every action is timestamped, identified, and hash-chained | `audit_trail.entries[]` |
| Is there tamper detection? | SHA-256 hash chain; any modification invalidates the chain | `immutability_proof.hash_chain[]`, `root_hash` |
| Who made decisions? | Signatures identify signers (human, AI, system) with timestamps | `signatures[].signer_id`, `signer_type`, `signed_at` |
| Are bundles retained? | Configurable retention (up to 7+ years for compliance) | `retention.retention_days`, `retention.policy` |

#### 7.2 Minimization and Reporting of Negative Impact

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Are risks identified and reported? | Policy evaluation findings flag issues by severity | `items[content_type=policy_evaluation].content.findings[].severity` |
| Are high-risk actions blocked? | L3/L4 changes require human approval; can block merge | `risk_tier`, `requires_approval`, `fail_on_high_risk` |
| Is there multi-perspective review? | 2-3 AI models review L2+ changes with consensus scoring | `models_used`, `consensus_risk`, `agreement_score` |

#### 7.3 Trade-offs

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Are trade-offs documented? | Model disagreements are tracked separately | `dissenting_opinions` |
| Are conditional decisions recorded? | Approvals can include conditions | `items[content_type=approval].content.conditions[]` |

#### 7.4 Redress

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Can past decisions be revisited? | Bundles are retained per compliance policy | `retention{}` |
| Can the decision chain be reconstructed? | Full audit trail preserved | `audit_trail.entries[]` |
| Can claims be independently verified? | guardspine-verify: `pip install guardspine-verify && guardspine-verify bundle.json` | Standalone tool |

---

### Requirement 1: Human Agency & Oversight (STRONG)

#### 1.1 Human Agency

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Do humans retain meaningful decision authority? | L3/L4 changes REQUIRE human approval; AI recommends but doesn't decide | `items[content_type=approval].content.approver.signer_type = "human"` |
| Can humans override AI recommendations? | Humans can approve despite AI concerns, or reject despite AI approval | `approval.decision` vs `consensus_risk` |

#### 1.2 Human Oversight

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Is there human-in-the-loop? | L4 (Critical) = mandatory HUMAN approval | `risk_threshold` config, `requires_approval` |
| Can oversight level be configured? | risk_threshold is configurable per branch/repo | `risk_threshold: L2|L3|L4` |
| Is the human oversight proportionate to risk? | Tier-based escalation: L0 = no review, L4 = mandatory human | `risk_tier` -> `models_used` -> `requires_approval` |

---

### Requirement 3: Privacy & Data Governance (STRONG via PII-Shield)

#### 3.1 Privacy

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Is personal data protected? | PII-Shield detects secrets and PII via entropy analysis, replaces with HMAC tokens | `sanitization.engine_name`, `sanitization.method` |
| Is sanitization documented? | Sanitization attestation records what was redacted | `sanitization.redaction_count`, `sanitization.redactions_by_type` |
| Is sanitization applied consistently? | Same salt = same HMAC token across all bundles | `sanitization.salt_fingerprint` |
| What pipeline stages are protected? | Tracks which outputs were sanitized | `sanitization.applied_to[]` (ai_prompt, pr_comment, evidence_bundle, sarif) |

#### 3.2 Data Quality & Integrity

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Is data integrity ensured? | Every content item is SHA-256 hashed | `items[].content_hash` |
| Can data modification be detected? | Hash chain detects any post-creation changes | `immutability_proof` |
| Is pre/post sanitization tracked? | Input and output hashes recorded | `sanitization.input_hash`, `sanitization.output_hash` |

---

### Requirement 2: Technical Robustness & Safety (MODERATE)

#### 2.1 Resilience to Attack and Security

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Is the system resistant to tampering? | SHA-256 hash chains, cryptographic signatures | `immutability_proof`, `signatures[]` |
| Are multiple signing algorithms supported? | Ed25519, RSA-SHA256, ECDSA-P256, HMAC-SHA256 | `signatures[].algorithm` |

#### 2.2 Accuracy

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Is the AI's assessment accurate? | Multi-model consensus reduces single-model errors | `models_used`, `agreement_score` |
| Is the assessment structured? | Rubric scoring provides quantified evaluation | Rubric-based policy evaluation |

#### 2.3 Reliability and Reproducibility

| ALTAI Sub-question | GuardSpine Evidence | Bundle Field |
|-------------------|--------------------|--------------|
| Can results be reproduced? | Deterministic hashing: same content = same hash every time | `content_hash = sha256(canonicalJSON(content))` |
| Is the spec versioned? | Schema version tracked in every bundle | `version: "0.2.1"` |

---

### Requirement 5: Diversity, Non-discrimination & Fairness (WEAK)

| ALTAI Sub-question | GuardSpine Evidence | Coverage |
|-------------------|--------------------|---------|
| Is there bias in AI decisions? | Multi-model review (diverse providers/architectures) reduces single-model bias | WEAK - diversity of models, not diversity of human perspectives |
| Is the system accessible? | Open source (MIT), standard JSON format, multiple verification methods (CLI, Docker, PyPI) | MODERATE - technical accessibility, not universal design |

**Gap**: GuardSpine does not currently assess code changes for discriminatory impact or fairness of AI outputs. A Z-Inspection rubric could add fairness-specific findings.

---

### Requirement 6: Societal & Environmental Well-being (WEAK)

| ALTAI Sub-question | GuardSpine Evidence | Coverage |
|-------------------|--------------------|---------|
| Is environmental impact considered? | Ollama local mode reduces cloud compute; models_used tracks resource consumption | WEAK |
| Is social impact assessed? | Risk tier prevents unchecked AI-generated code from shipping to production | WEAK - indirect social protection |

**Gap**: GuardSpine does not measure carbon footprint, social impact, or democratic implications. These remain manual Z-Inspection assessment areas.

---

## Part 4: Z-Inspection Process Step Mapping

How GuardSpine artifacts support each Z-Inspection step:

| Z-Inspection Step | GuardSpine Support | Coverage |
|-------------------|-------------------|----------|
| 1. Pre-conditions | `metadata{}` can store pre-condition checks; `policy_id` references governance framework | MODERATE |
| 2. Team formation | `signatures[].signer_id` identifies team members; `approver{}` records human reviewers | STRONG |
| 3. Protocol documentation | **The entire bundle IS the protocol.** Hash-chained, timestamped, signed event log. | STRONG |
| 4. Boundary definition | `scope{}` with artifact_id, version_from/to, assertion_type; `risk_tier` defines severity boundary | STRONG |
| 5. Socio-technical scenarios | `items[content_type=diff]` shows technical change; `policy_evaluation` shows policy context; `risk_drivers` show impact | MODERATE |
| 6. Ethical issue identification | `items[content_type=policy_evaluation].findings[]` identify issues; rubric evaluation applies compliance frameworks | MODERATE |
| 7. Trustworthy AI mapping | **KEY GAP.** GuardSpine maps to SOC2/HIPAA/PCI-DSS but NOT to ALTAI 7 requirements. | GAP |
| 8. Execution | CodeGuard GitHub Action runs automatically on every PR - continuous execution | STRONG |
| 9. Resolution & maintenance | `approval` items with decision/rationale/conditions; `retention{}` for long-term maintenance | STRONG |

---

## Part 5: Integration Proposal

### 5.1 New Rubric: `z-inspection.yaml`

Create a custom rubric that maps GuardSpine findings to ALTAI requirements:

```yaml
# .guardspine/rubrics/z-inspection.yaml
name: Z-Inspection Trustworthy AI Assessment
version: 1.0.0
framework: EU-ALTAI-2020
description: Maps code change evidence to Z-Inspection ALTAI requirements

requirements:
  transparency:
    altai_ref: "Requirement 4"
    sub_requirements:
      traceability:
        evidence_types: [diff, policy_evaluation, approval]
        required_fields: [content_hash, created_at, sequence]
        assessment: "Are all decision steps recorded with timestamps and hashes?"
      explainability:
        evidence_types: [policy_evaluation]
        required_fields: [findings, rationale]
        assessment: "Can each risk classification be explained with specific findings?"
      communication:
        evidence_types: [approval]
        required_fields: [decision, rationale]
        assessment: "Are stakeholders informed of AI involvement and risk level?"

  accountability:
    altai_ref: "Requirement 7"
    sub_requirements:
      auditability:
        evidence_types: [immutability_proof, signatures]
        required_fields: [hash_chain, root_hash, signer_id]
        assessment: "Can an independent third party verify this bundle without vendor access?"
      impact_minimization:
        evidence_types: [policy_evaluation]
        required_fields: [findings, severity]
        assessment: "Are high-risk findings identified and blocking where appropriate?"
      redress:
        evidence_types: [approval, retention]
        required_fields: [retention_days, audit_trail]
        assessment: "Can past decisions be revisited with full context?"

  human_oversight:
    altai_ref: "Requirement 1"
    sub_requirements:
      human_agency:
        evidence_types: [approval]
        required_fields: [approver.signer_type, decision]
        assessment: "Did a human make the final decision for high-risk changes?"
      proportionality:
        evidence_types: [risk_tier]
        assessment: "Is oversight level proportionate to risk tier?"

  privacy:
    altai_ref: "Requirement 3"
    sub_requirements:
      data_protection:
        evidence_types: [sanitization]
        required_fields: [engine_name, redaction_count, status]
        assessment: "Was PII-Shield sanitization applied before external data sharing?"
      data_integrity:
        evidence_types: [immutability_proof]
        required_fields: [content_hash, root_hash]
        assessment: "Is data integrity provable via hash chain?"

  robustness:
    altai_ref: "Requirement 2"
    sub_requirements:
      tamper_resistance:
        evidence_types: [immutability_proof, signatures]
        assessment: "Is the evidence chain cryptographically tamper-evident?"
      accuracy:
        evidence_types: [policy_evaluation]
        required_fields: [models_used, agreement_score]
        assessment: "Was multi-model consensus used to reduce single-model error?"
```

### 5.2 Bundle Metadata Extension

Add Z-Inspection phase tracking to bundle metadata:

```json
{
  "metadata": {
    "z_inspection": {
      "assessment_id": "ZI-2026-0042",
      "phase": "assess",
      "step": 7,
      "assessor_team": ["ishwar.chavhan", "david.youssef"],
      "altai_coverage": {
        "transparency": { "status": "evidenced", "items": ["item-001", "item-002", "item-003"] },
        "accountability": { "status": "evidenced", "items": ["item-001", "item-003"] },
        "human_oversight": { "status": "evidenced", "items": ["item-003"] },
        "privacy": { "status": "evidenced", "items": ["sanitization"] },
        "robustness": { "status": "evidenced", "items": ["immutability_proof"] },
        "fairness": { "status": "manual_required", "items": [] },
        "societal_wellbeing": { "status": "manual_required", "items": [] }
      },
      "ethical_tensions": [],
      "recommendations": []
    },
    "retention": {
      "policy": "regulatory",
      "retention_days": 2555
    }
  }
}
```

### 5.3 Z-Inspection Assessment Report Export

Generate a Z-Inspection-compatible report from evidence bundles:

```
Z-INSPECTION ASSESSMENT REPORT
================================
Assessment ID: ZI-2026-0042
Bundle ID: b7e3f8a2-4c1d-9e5b-6a7f-8c0d1e2b3a4c
Artifact: github:acme/payments-api/src/api/payments.py
Risk Tier: L3 (High)
Date: 2024-01-15T14:30:00Z

ALTAI REQUIREMENT COVERAGE
---------------------------
[EVIDENCED] R1 Human Oversight: Human approval by Sarah Chen (L3 = mandatory)
[EVIDENCED] R2 Robustness: SHA-256 hash chain (3 links), Ed25519 signatures (2)
[EVIDENCED] R3 Privacy: PII-Shield sanitized (3 redactions: 1 email, 2 api_keys)
[EVIDENCED] R4 Transparency: 3 evidence items, full hash chain, policy findings
[MANUAL]    R5 Fairness: No automated assessment (requires human evaluation)
[MANUAL]    R6 Societal: No automated assessment (requires human evaluation)
[EVIDENCED] R7 Accountability: Audit trail (5 entries), 7-year retention, offline-verifiable

EVIDENCE CHAIN
--------------
Seq 0: diff         -> sha256:8a7b6c5d... (code change snapshot)
Seq 1: policy_eval  -> sha256:3c4d5e6f... (SOC2 CC6.1 evaluation: PASS)
Seq 2: approval     -> sha256:2b3c4d5e... (Sarah Chen: approved with conditions)
Root Hash: sha256:9e8f7a6b...

VERIFICATION: pip install guardspine-verify && guardspine-verify bundle.json
```

---

## Part 6: Coverage Summary

### ALTAI Requirements Coverage Matrix

| # | ALTAI Requirement | Coverage | Automated? | GuardSpine Evidence |
|---|-------------------|----------|------------|---------------------|
| 1 | Human Agency & Oversight | STRONG | Yes | Tier-based human approval, override capability |
| 2 | Technical Robustness & Safety | MODERATE | Yes | Hash chains, multi-model consensus, signatures |
| 3 | Privacy & Data Governance | STRONG | Yes | PII-Shield sanitization, integrity proofs |
| 4 | Transparency | STRONG | Yes | Hash-chained event log, findings, rationale |
| 5 | Diversity & Fairness | WEAK | No | Multi-model diversity only; no fairness assessment |
| 6 | Societal Well-being | WEAK | No | Indirect only (risk gating) |
| 7 | Accountability | STRONG | Yes | Tamper-evident audit trail, offline verification |

**Result**: 4 of 7 requirements have STRONG automated coverage. 1 has MODERATE. 2 require manual Z-Inspection assessment (fairness, societal impact).

### Z-Inspection Process Step Coverage

| Phase | Steps Covered | Steps Partially Covered | Gaps |
|-------|---------------|------------------------|------|
| Set Up (1-4) | 2, 3, 4 | 1 | None significant |
| Assess (5-7) | - | 5, 6 | 7 (ALTAI mapping rubric needed) |
| Resolve (8-9) | 8, 9 | - | None |

---

## Part 7: Open Questions for Ishwar

1. **Rubric structure**: Does the proposed `z-inspection.yaml` rubric align with how Z-Inspection assessors actually work? Should it be organized differently?

2. **Evidence sufficiency**: For each ALTAI requirement marked STRONG, would a Z-Inspection assessor accept an evidence bundle as sufficient documentation, or would they need additional manual artifacts?

3. **Phase tracking**: Is the proposed `z_inspection` metadata extension useful? Should it track more granular phase state?

4. **Ethical tensions**: Z-Inspection identifies "ethical tensions" in Step 6. Could these be represented as a new evidence item type (`content_type: "ethical_tension"`) with fields for the tension description, stakeholders affected, and proposed resolution?

5. **Continuous vs point-in-time**: Z-Inspection is designed as a point-in-time assessment. If GuardSpine produces evidence bundles on every PR, how should Z-Inspection adapt? Periodic sampling? Aggregate reports? Dashboard?

6. **ALTAI question coverage**: The ALTAI checklist has 100+ specific questions. Which subset is most relevant to AI-mediated code changes specifically (vs. broader AI system assessment)?

7. **Requirements 5 & 6**: What would a fairness and societal impact assessment look like for a code governance tool? Is there a meaningful way to automate any portion?

---

## References

- Z-Inspection: https://z-inspection.org/
- Z-Inspection IEEE paper: Zicari et al., "Z-Inspection: A Process to Assess Trustworthy AI", IEEE TTS, 2021
- ALTAI: https://digital-strategy.ec.europa.eu/en/library/assessment-list-trustworthy-artificial-intelligence-altai-self-assessment
- EU Ethics Guidelines: https://digital-strategy.ec.europa.eu/en/library/ethics-guidelines-trustworthy-ai
- GuardSpine Spec: https://github.com/DNYoussef/guardspine-spec (v0.2.1)
- GuardSpine CodeGuard: https://github.com/DNYoussef/codeguard-action
- PII-Shield: https://github.com/aragossa/pii-shield
