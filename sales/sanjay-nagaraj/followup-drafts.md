# Sanjay — Post-Zoom Follow-Up Drafts

## Draft A: Strong Interest (pilot agreement)
Subject: GuardSpine pilot — next steps for [repo name]

Sanjay — thanks for the conversation today. Three things to make the pilot frictionless:

1. **Installation**: I'll send a PR to add the GitHub Action to [agreed repo]. Takes 5 minutes to merge. Nothing changes in your workflow — it only adds evidence generation on PRs.

2. **First evidence**: Within 24 hours of the first PR, you'll have hash-chained evidence bundles. I'll send you a sample with annotations showing what maps to which SOC 2 control.

3. **2-week check-in**: I'll compile a report after 2 weeks — tier distribution, auto-classify rate, evidence bundle count, and what your auditor would see.

No cost, no contract, no access beyond read-only on diffs. If it's not useful after 2 weeks, uninstall the Action in 30 seconds.

Talk soon,
David

## Draft B: Interest but no commitment
Subject: The evidence bundle from our call

Sanjay — enjoyed the conversation. Attaching the evidence bundle I showed you (bundle-pr3-49c66f0.json). Two things worth noting:

1. The hash chain is real — you can verify it independently. Each event's hash includes the previous event's hash. Modification breaks the chain.

2. The tier model I walked through (L0-L4) is the same one we use on our own repos. The $44/month number at 100 PRs/day isn't theoretical — it's what we actually spend.

When you're ready to see it on a Harness repo, the install is a single YAML file. Happy to send over whenever.

Best,
David

## Draft C: Lukewarm / redirected to team
Subject: GuardSpine one-pager for [team lead name]

Sanjay — thanks for pointing me to [team lead]. Attaching our one-pager and the raw evidence bundle from the demo.

The shortest path to evaluate: install our GitHub Action on one repo (5-minute PR, read-only, free). If the evidence bundles map to what [team lead]'s auditors need, we expand. If not, 30-second uninstall.

Happy to jump on a call with [team lead] whenever works.

David
