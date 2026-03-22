# GuardSpine GTM Execution Plan
## ARO + Hormozi Recursive Learning Loop + Existing Infrastructure

**Date**: 2026-03-22
**Author**: GuardSpine Ops Agent
**Source**: David Youssef GTM thread (#gtm), Hormozi ad strategy analysis, ARO framework
**Status**: DRAFT — awaiting David approval

---

## The Thesis

Marketing is being redefined from campaign craftsmanship into recursive preference learning. The economic winner is whoever can most efficiently convert audience behavior into proprietary, compounding judgment.

We already have 80% of the system. The missing 20% is attribution — without it, the learning loop learns nothing.

---

## Architecture: The Recursive Learning Loop

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│  1. DISCOVER (Narrowcast)                          │
│     n8n M31, W-Draft-Followups                     │
│     → Find warm leads on Reddit, dev.to, LinkedIn  │
│                                                     │
│  2. DRAFT (Content-Drafter + Scoring Rubric)       │
│     Content-drafter skill + W-Creative-Scorer       │
│     → Generate 10 hooks × 3 bodies per lead        │
│     → Score against rubric BEFORE posting           │
│                                                     │
│  3. POST (David reviews + posts)                   │
│     → Reddit comments, dev.to, email, LinkedIn DM  │
│     → Record: message_id, platform, posted_at       │
│                                                     │
│  4. MEASURE (W-Outreach-Tracker)                   │
│     Daily cron scans for engagement on posted msgs  │
│     → Upvotes, replies, DMs, saves, follows         │
│     → Store in message_drafts table                 │
│                                                     │
│  5. ATTRIBUTE (W-Attribution-Bridge)               │
│     Landing page signup → match to outreach source  │
│     → Tag originating message as "converted"        │
│     → Revenue-linked outcome data                   │
│                                                     │
│  6. LEARN (W-Creative-Scorer)                      │
│     Pull top 5 + bottom 5 by outcome               │
│     → LLM: "What patterns separate winners/losers?" │
│     → Store rubric in memory-mcp                    │
│     → Rubric improves every cycle                   │
│                                                     │
│  ↻ REPEAT (weekly cycle, compounding)              │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## Phase 1: ATTRIBUTION (Week 1) — The Foundation

**Why first**: Without attribution, every subsequent phase learns from noise. This is the Hyros equivalent for our B2B text-first pipeline.

### 1.1 Database Schema Changes

Add to `outreach.db`:

```sql
-- Extend message_drafts table
ALTER TABLE message_drafts ADD COLUMN posted_at TEXT;
ALTER TABLE message_drafts ADD COLUMN posted_platform TEXT;
ALTER TABLE message_drafts ADD COLUMN posted_url TEXT;
ALTER TABLE message_drafts ADD COLUMN engagement_upvotes INTEGER DEFAULT 0;
ALTER TABLE message_drafts ADD COLUMN engagement_replies INTEGER DEFAULT 0;
ALTER TABLE message_drafts ADD COLUMN engagement_dms INTEGER DEFAULT 0;
ALTER TABLE message_drafts ADD COLUMN engagement_saves INTEGER DEFAULT 0;
ALTER TABLE message_drafts ADD COLUMN engagement_score REAL DEFAULT 0;
ALTER TABLE message_drafts ADD COLUMN converted_at TEXT;
ALTER TABLE message_drafts ADD COLUMN conversion_type TEXT; -- demo_request, signup, meeting
ALTER TABLE message_drafts ADD COLUMN revenue_attributed REAL DEFAULT 0;
ALTER TABLE message_drafts ADD COLUMN attribution_source TEXT;
ALTER TABLE message_drafts ADD COLUMN scoring_rubric_version INTEGER DEFAULT 0;
ALTER TABLE message_drafts ADD COLUMN predicted_score REAL;
ALTER TABLE message_drafts ADD COLUMN actual_outcome TEXT; -- winner, loser, mid

-- Scoring rubric table
CREATE TABLE IF NOT EXISTS scoring_rubrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    rubric_json TEXT NOT NULL, -- full rubric as JSON
    training_data_count INTEGER,
    accuracy_vs_previous REAL,
    notes TEXT
);
```

### 1.2 W-Attribution-Bridge (new n8n workflow)

- **Trigger**: Webhook from landing page (`/api/signup` and `/api/demo-request`)
- **Logic**:
  1. Receive signup/demo-request payload (email, company, source, UTMs)
  2. Query outreach.db for matching email/company in contacts
  3. If match found → update message_drafts with `converted_at`, `conversion_type`
  4. Post to #pipeline: "🎯 Attribution: [email] from [platform] → matched to outreach [message_id]"
  5. Seal evidence bundle

### 1.3 Wire Landing Page Webhook

Set `N8N_WEBHOOK_URL` on landing page Railway service (project `1a6b984a`) to point to `https://n8n-production-7528.up.railway.app/webhook/outreach-pipeline` with action `check_landing_signups`.

---

## Phase 2: MEASUREMENT (Week 2) — Track What Happens After Posting

### 2.1 W-Outreach-Tracker (new n8n workflow)

- **Trigger**: Daily cron (6am ET)
- **Logic**:
  1. Query message_drafts for messages with `posted_url IS NOT NULL AND posted_at > 7 days ago`
  2. For each posted message:
     - Reddit: fetch upvotes/comments via Reddit JSON API (`{url}.json`)
     - dev.to: fetch reactions via dev.to API
     - LinkedIn: manual tracking (no public API — David reports via Slack)
  3. Update engagement scores in outreach.db
  4. Calculate composite score: `engagement_score = (upvotes * 1) + (replies * 3) + (DMs * 10) + (saves * 5)`
  5. Weekly summary to #pipeline

### 2.2 Engagement → Outcome Classification

After 14 days of data:
- `engagement_score > 75th percentile` → tag as "winner"
- `engagement_score < 25th percentile` → tag as "loser"
- Middle → tag as "mid"

---

## Phase 3: LEARNING (Week 3) — Build the Scoring Rubric

### 3.1 W-Creative-Scorer (evolve W-Content-Chain-Generator)

- **Trigger**: Weekly cron (Monday 7am ET) + on-demand via webhook
- **Logic**:
  1. Pull all messages classified as winner/loser/mid from outreach.db
  2. LLM call to Claude via LiteLLM:

  ```
  Here are our top-performing outreach messages (by engagement + conversion):
  [winners]

  Here are our worst-performing messages:
  [losers]

  Analyze the patterns. What specifically makes winners win and losers lose?
  Consider: hook construction, pain specificity, evidence density, CTA framing,
  platform fit, prospect lane (builder/buyer/connector/investor), timing.

  Output a scoring rubric with 10 weighted criteria. Each criterion 1-10.
  Include specific examples of good vs bad for each criterion.
  ```

  3. Store rubric in scoring_rubrics table + memory-mcp
  4. Version-increment the rubric
  5. Post rubric summary to #pipeline

### 3.2 Pre-Post Scoring

When content-drafter generates new messages:
1. Score each draft against current rubric
2. Flag any draft scoring below threshold
3. Include score + reasoning in #pipeline post
4. David sees: "Draft for [lead], predicted score: 7.8/10 — [reasoning]"

---

## Phase 4: GENERATION (Week 4) — Rubric-Guided Content Creation

### 4.1 Enhanced Content-Drafter Skill

Update `/app/skills/content-drafter/SKILL.md`:
- Input: prospect data + scoring rubric + narrowcast context
- Output: 10 hook variations × 3 body variations = 30 candidates
- Auto-score all 30, surface top 5 to David
- Include "why this hook works" reasoning from rubric

### 4.2 Hormozi Hook Pattern

Based on the analysis: hooks are massive outliers. Generate disproportionately more hooks per body:
- 10 hooks (first sentence variations)
- 3 bodies (core message variations)
- David picks best hook + body combo

### 4.3 Competitor Angle Mining

Narrowcast already scans competitor content. Add:
- Extract hooks from high-engagement competitor posts
- Feed into variation generator as "angles to explore"
- Weight lower than own data (per Hormozi principle)

---

## Phase 5: ARO Implementation (Ongoing)

### 5.1 Landing Page ARO (PR #2 — already shipped)

- ✅ Comparison table (GuardSpine vs Vanta/Drata/Secureframe/Snyk)
- ✅ JSON-LD schema markup
- ✅ Decision checklist
- ✅ Epistemic framing

### 5.2 Entity Consistency Campaign

Ensure identical definition everywhere:

> **GuardSpine** is an artifact governance platform that generates cryptographic evidence bundles proving what was reviewed, by whom, when, and against what criteria.

Surfaces to update:
- [ ] guardspine.ai (landing page)
- [ ] GitHub org description
- [ ] LinkedIn company page
- [ ] Crunchbase profile (create)
- [ ] G2 listing (create)
- [ ] npm/PyPI package descriptions

### 5.3 Query Ownership Pages (Phase 2 — after attribution works)

One structured page per target query:
- "AI code governance tools comparison"
- "How to audit AI-generated code"
- "SOC 2 compliance for AI agents"
- "Best practices for AI code review"
- "LLM output validation tools"

---

## KPIs and Counter-KPIs

| KPI | Counter-KPI | Target (30 days) |
|---|---|---|
| Messages posted/week | Reply rate per message | 10 msgs/wk, >15% reply |
| Demo requests from outreach | Time-to-demo from first contact | 3 demos, <7 days |
| Pipeline value ($) | Pipeline velocity (days) | $50k pipeline, <30 day velocity |
| Narrowcast leads found/week | Leads that convert to conversation | 15 leads, >20% conversation |
| Landing page signups | Signup-to-demo conversion | 20 signups, >10% to demo |
| Scoring rubric accuracy | Rubric drift (predicted vs actual) | >60% prediction accuracy |
| Evidence bundles produced | Bundles cited in sales | 10 bundles, >3 cited |

---

## Infrastructure Mapping

| Component | Tool | Status |
|---|---|---|
| Lead discovery | n8n narrowcast workflows (M31, scans) | ✅ Running |
| Content drafting | Content-drafter skill + Claude via LiteLLM | ✅ Available |
| Draft scoring | W-Creative-Scorer (new) | 🔨 Build Week 3 |
| Posting tracking | W-Outreach-Tracker (new) | 🔨 Build Week 2 |
| Attribution | W-Attribution-Bridge (new) | 🔨 Build Week 1 |
| Knowledge store | memory-mcp v1.5.0 | ✅ Running |
| Scoring rubrics | outreach.db + memory-mcp | 🔨 Schema Week 1 |
| Agent orchestration | Paperclip (CMO, Content Director) | ⏳ Activate after data |
| ARO pages | guardspine-landing repo | ✅ PR #2 shipped |
| Evidence sealing | guardspine-internal ops_evidence | ✅ Running |
| Workflow engine | n8n (94 workflows) | ✅ Running |

---

## What We Are NOT Building

- Meta/Instagram API integration (we're B2B, not DTC)
- Video transcription pipeline (our content is text-first)
- Synthetic audience avatars (premature — need real data first)
- Paid ad management (premature — organic-first until we have attribution)
- Full Hyros integration (overkill — our landing page webhook is sufficient)

---

## Decision Needed from David

1. **Approve Phase 1 start?** (Attribution bridge + schema changes — I can build this tonight)
2. **Which landing page Railway project token to use?** (Need to set N8N_WEBHOOK_URL on project `1a6b984a`)
3. **Will you report LinkedIn engagement manually via Slack?** (No public API — I can build a simple `/engage` command)
4. **Budget for G2 listing?** ($0 to create basic profile, paid for reviews/badges)
5. **Crunchbase profile — do you want to create this?** (Free founder profile)

---

## Timeline

| Week | Focus | Deliverable |
|---|---|---|
| Week 1 (Mar 23-29) | Attribution + Schema | W-Attribution-Bridge live, outreach.db updated, webhook wired |
| Week 2 (Mar 30-Apr 5) | Measurement | W-Outreach-Tracker live, engagement data flowing |
| Week 3 (Apr 6-12) | Learning | W-Creative-Scorer v1, first rubric generated |
| Week 4 (Apr 13-19) | Generation | Rubric-guided drafts, 10-hook pattern, automated scoring |
| Ongoing | Compound | Rubric improves weekly, data compounds, selection probability rises |

**The moat builds from Week 1. Every day without attribution is a day the loop can't learn.**
