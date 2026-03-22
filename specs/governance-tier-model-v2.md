# GuardSpine Governance Tier Model v2.0

## Design Principle
Risk tiers scale linearly with model count. Inspired by Nassim Taleb's barbell strategy:
- L0-L1 = safe side (cheap, fast, deterministic — handles 80% of changes)
- L3-L4 = aggressive side (expensive but catches tail risks that destroy trust)
- L2 = middle — use when you need cross-validation but not full council

## Tier Definitions

### L0 — Rules-Based Only
- **Models**: 0
- **Method**: Pattern matching, file heuristics, diff size, path analysis, sensitive zone detection
- **Cost**: $0
- **Latency**: <2 seconds
- **Use when**: Test files, docs, non-sensitive configs, small diffs (<50 lines)
- **Outcome**: Auto-approve or escalate to L1
- **Evidence**: Diff hash, risk scores, file classification

### L1 — Single Model Review
- **Models**: 1 (default: gpt-4o-mini via LiteLLM)
- **Method**: One LLM reviews against rubric. Classifies risk, identifies concerns, recommends action.
- **Cost**: ~$0.01/review
- **Latency**: 5-15 seconds
- **Use when**: Application code changes, config changes to non-critical systems, dependency updates
- **Outcome**: Approve, flag for L2, or reject
- **Evidence**: Model response, rubric match scores, risk classification rationale

### L2 — Dual Model Review
- **Models**: 2 (default: gpt-4o-mini + claude-haiku)
- **Method**: Two independent LLMs review same diff against rubric. Disagreements auto-escalate to L3.
- **Cost**: ~$0.03/review
- **Latency**: 10-25 seconds
- **Use when**: Changes touching auth, payments, PII zones, infrastructure configs, CI/CD pipelines
- **Outcome**: Approve (if both agree), escalate to L3 (if disagree), or reject
- **Evidence**: Both model responses, agreement/disagreement matrix, escalation reason

### L3 — Three Model Council
- **Models**: 3 (default: gpt-4o-mini + claude-haiku + gemini-flash)
- **Method**: Full council review. All three review independently. Majority rules, but unanimous disagreement blocks.
- **Cost**: ~$0.05/review
- **Latency**: 15-40 seconds
- **Use when**: Changes to governance rules, security policies, encryption configs, production database schemas
- **Outcome**: Approve (2/3+ agree), block (unanimous concern), or escalate to L4
- **Evidence**: All three responses, voting record, dissent reasons, council summary

### L4 — Council + Mandatory Human Approval
- **Models**: 3 (same council as L3)
- **Method**: Council reviews AND human must explicitly approve. No auto-approve path.
- **Cost**: ~$0.05 + human time
- **Latency**: Minutes to hours (human-dependent)
- **Use when**: Changes to the governance system itself, credential rotation, production deployment gates, compliance-critical changes
- **Outcome**: Requires explicit human "APPROVED" signal. Council provides recommendation only.
- **Evidence**: Council recommendation + human approval record + timestamp + approver identity

## Escalation Rules
- L0 → L1: When rules detect semantic complexity beyond pattern matching
- L1 → L2: When single model confidence is below threshold or flags uncertainty
- L2 → L3: When two models disagree on risk classification
- L3 → L4: When any model flags "requires human judgment" or change touches governance rules
- Any tier can escalate UP but never DOWN

## Cost Model
| Tier | Models | Cost/Review | Monthly (100 PRs/day) | Handles |
|------|--------|------------|----------------------|---------|
| L0 | 0 | $0 | $0 | ~70% of changes |
| L1 | 1 | $0.01 | $9 | ~20% of changes |
| L2 | 2 | $0.03 | $18 | ~7% of changes |
| L3 | 3 | $0.05 | $15 | ~2.5% of changes |
| L4 | 3+human | $0.05+ | $1.50+ | ~0.5% of changes |
| **Total** | | | **~$43.50/mo** | **100%** |

## Taleb Risk Mapping
- **Fragile path**: Skipping tiers (going L0 on everything). Saves money, misses tail risk.
- **Robust path**: L1 on everything. Catches most issues. Costs ~$30/mo at scale.
- **Antifragile path**: Dynamic tier assignment based on historical data. The system learns which file paths, authors, and change patterns need higher tiers. Every L3/L4 failure teaches L0/L1 to catch it earlier next time.

## Implementation
- CodeGuard action: `risk_threshold` parameter sets the minimum tier
- LiteLLM handles model routing: `gpt-4o-mini`, `claude-haiku`, `gemini-flash`
- Evidence bundles include tier, model count, and all model responses
- Escalation is automatic; de-escalation requires explicit config change
