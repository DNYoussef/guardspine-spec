# GuardSpine ROI Model — Harness Scale

## Assumptions
- Harness engineering: ~500 developers (estimated from team size + Traceable merge)
- Average PRs/day: 200 (conservative for 500 devs)
- Current review overhead: 15 min avg per PR for compliance-relevant review
- Compliance audit prep: 2 FTEs spend ~20% time on evidence gathering
- SOC 2 audit cost: $150K-300K/year (Type II)

## Current State (without GuardSpine)
| Item | Monthly Cost |
|------|-------------|
| Developer review time (200 PRs × 15 min × $80/hr) | $40,000 |
| Audit evidence gathering (0.4 FTE × $12K/mo) | $4,800 |
| Audit prep sprints (2x/year, 2 weeks each, 3 people) | $5,000/mo amortized |
| SOC 2 audit fees | $18,750/mo amortized |
| **Total** | **$68,550/mo** |

## With GuardSpine
| Item | Monthly Cost |
|------|-------------|
| GuardSpine (200 PRs/day, tier distribution) | $44 |
| Reduced review time (70% of PRs auto-classified L0-L1, skip deep review) | $12,000 |
| Audit evidence: auto-generated (0.05 FTE remaining) | $600 |
| Audit prep: evidence bundles replace manual gathering | $1,000/mo amortized |
| SOC 2 audit fees (faster audit with structured evidence) | $12,500/mo amortized |
| **Total** | **$26,144/mo** |

## Delta
| Metric | Value |
|--------|-------|
| Monthly savings | $42,406 |
| Annual savings | $508,872 |
| GuardSpine annual cost (at scale pricing TBD) | ~$12,000-60,000 |
| ROI | 8x-42x |
| Payback period | < 1 month |

## Non-Financial Value
1. **Audit readiness**: Always audit-ready, not sprint-to-prepare
2. **Developer velocity**: 70% of PRs need no manual compliance review
3. **Regulatory defense**: Tamper-proof evidence chain for EU AI Act, SOC 2, FedRAMP
4. **Customer trust**: Can demonstrate governance to Harness's own customers

## Pilot Proposal (Zero Risk)
- Duration: 2 weeks
- Scope: 1 internal repo
- Cost: $0 (GitHub Action is free)
- Effort: 5 min to install, 0 ongoing
- Output: Evidence bundles for every PR, risk classification, audit report
- Success criteria: "Would you want this on more repos?"

*Note: Dollar figures use industry benchmarks. Actual Harness numbers should be validated during discovery call.*
