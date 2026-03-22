# Sanjay Zoom Demo Script — 10 Minutes

## Setup (pre-call)
- Have Bundle #001 JSON open in browser tab (raw evidence)
- Have guardspine-spec PR #3 open (the PR that generated it)
- Have the CodeGuard action run page open (shows 18-second governance)
- Have the evidence-bundle-library.md visible (the artifact that was governed)

## Flow

### Minute 0-2: Hook
"Sanjay, before we get into slides — I want to show you something we built last night. 
It's not a demo environment. It's our actual production system governing its own changes."

[Show PR #3 on guardspine-spec]

"This is a real pull request on our specification repo. When I pushed this commit, 
CodeGuard — our GitHub Action — ran automatically. It analyzed the diff, classified 
the risk, and produced a tamper-proof evidence bundle. The whole thing took 18 seconds."

### Minute 2-4: The Evidence Bundle
[Show Bundle #001 JSON]

"This is what came out. It's not a log file. It's a cryptographically hash-chained 
evidence bundle. Every event — the PR submission, the analysis, the risk classification — 
is individually hashed, and each hash chains to the previous one."

Point out:
- `hash_chain.algorithm: sha256`
- `immutability_proof.hash_chain` — genesis → chain_hash → chain_hash
- `summary.risk_tier: L1`
- `summary.requires_approval: false` (auto-approved at L1)

"If anyone modifies this bundle after the fact — even one character — the hash chain breaks. 
That's the compliance guarantee."

### Minute 4-6: The Tier Model
"You asked about how we handle different risk levels. Here's our model:"

[Show governance-tier-model-v2.md]

"L0 is rules-based. No AI, no cost, sub-2-second. Handles 70% of changes.
L1 adds one model — catches semantic issues rules miss.
L2 adds a second model — cross-validates.
L3 is a three-model council — for changes to security policies and governance rules.
L4 is council plus mandatory human approval. No auto-approve path."

"For Harness at scale — say 100 PRs a day — the cost model is about $44/month total. 
The L0 tier alone eliminates most of the review bottleneck."

### Minute 6-8: The Harness Angle
"Harness handles everything after code is written — build, test, deploy, verify. 
GuardSpine proves the change was governed before it deploys."

"Your AppSec team just launched AI code security features. That's analyzing code 
for vulnerabilities. We're analyzing changes for governance compliance. 
Different questions, same pipeline position."

"The integration would be: your customer pushes code → CodeGuard classifies and 
evidence-seals at PR time → Harness deploys with the evidence bundle attached → 
auditors verify the bundle months later without touching the pipeline."

### Minute 8-10: The Ask
"We're not asking Harness to build this. We're asking whether this belongs in 
the Harness ecosystem — as a marketplace action, an integration, or a partnership."

"The pilot would be: pick one internal Harness repo. Install the GitHub Action. 
Run it for 2 weeks. Evaluate the evidence bundles against your SOC 2 requirements. 
Zero risk — it's a GitHub Action, it reads diffs, it writes evidence. It doesn't 
modify code or block deploys unless you configure it to."

Three questions for Sanjay:
1. "Does your AppSec team face evidence-of-review requests from customers or auditors?"
2. "How do you currently demonstrate to SOC 2 auditors that code changes were reviewed?"
3. "Would a 2-week no-cost pilot on one repo be worth your team's time?"
