# Templates and Recommended Pages

## SCHEMA.md Template

```markdown
# Wiki Schema

## Domain
[Business process, function, or operating domain this wiki grounds.]

## Purpose
This wiki grounds a Digital Worker by distilling source cases into reusable topic,
process, role, playbook, automation, governance, and evaluation knowledge.
Cases are cited, never copied: per-case detail lives in `_meta/ingest-ledger.csv`.

## Conventions
- File names: lowercase, hyphenated, no spaces; named for topics, never for batches or cases.
- Every page starts with the frontmatter defined in `references/provenance.md`
  (control files are exempt: SCHEMA.md, index.md, log.md).
- Every claim carries an inline citation: `(evidence: N cases — e.g. ID1, ID2)`.
- Pages use `[[wikilinks]]`; new pages are added to `index.md` in the same edit.
- Every ingest/query/lint action is appended to `log.md` as
  `## [YYYY-MM-DD] <mode> | <scope>` followed by one-line outcome bullets.
- `_meta/knowledge.db` is refreshed after batch checkpoints and major rewrites. It indexes cases, pages, cited claims, claim→case links, and sanitized reusable data points for audit/search; it never stores raw source narratives.
- Pages stay under ~200 lines; split by topic when they grow past that.

## Taxonomy
[Per axis — case_type, topic, process_stage, root_cause, resolution_pattern, actors,
systems — list the current categories with a one-line definition each. The `topic`
axis is the largest: expect dozens of specific categories on a large corpus, each
concrete enough to name a real page (`orchestrator-certificate-renewal`, not
`technical-issue`); other axes typically hold 5-15 each. Mark categories
`(provisional)` until stabilization. Categories are added only via the
pending-categories process; any category exceeding 15% share on topic/root_cause/
resolution_pattern must be decomposed.]

## Update Policy
Conflicting evidence: keep both claims with citations and dates, mark the claim
line `⚠ contested` (page-level `contested: true` only when the central claim is
disputed), flag in log/batch report. Never silently overwrite.
```

## index.md Skeleton

```markdown
# Index

## Process
- [[process/overview]] — end-to-end stage map.

## Concepts
- [[concepts/business-object-model]] — objects, fields, lifecycle.

[...one section per top-level directory; every durable page listed exactly once
with a one-line summary.]
```

## log.md Skeleton

```markdown
# Log

## [YYYY-MM-DD] init | wiki created
- Domain: <domain>. SCHEMA.md, index.md written.
```

## Topic Map (`_meta/topic-map.md`)

Create once the wiki passes ~75 pages; refresh at batch checkpoints. A one-screen
navigation aid — topic clusters mapped to their pages, denser than index.md:

```markdown
# Topic Map

## <Topic cluster>
[[concepts/page-a]] · [[concepts/page-b]] · [[process/stages/stage-x]]

## <Topic cluster>
...
```

## Topic Page Template (`concepts/`)

Target 60–200 lines. Every section carries the actual substance — error signatures, versions, step-by-step procedures — at the depth defined in `references/extraction.md`. A topic page thinner than ~40 lines while citing 20+ cases is a lint finding, not a page.

```markdown
---
title: <Topic>
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: topic
tags: [...]
exemplars: [case IDs]
confidence: high
contested: false
---

# <Topic>

One paragraph: what this topic is, when the worker encounters it, why it matters.

## Symptoms & signals
- <How instances present: verbatim error messages, log lines, codes, user reports —
  sanitized but exact>. (evidence: N cases — e.g. ID1, ID2)

## Patterns
### <Specific named pattern, one subsection per pattern>
**Symptom**: <exact presentation, error signature>. (evidence: ...)
**Cause**: <why it happens; environment/version preconditions>. (evidence: ...)
**Resolution**:
1. <Actual step — command, config key, UI path, verification>.
2. <...every step, in order, with <placeholders> for instance-specific values>.
(evidence: N cases — e.g. ID1, ID2)
**Variants**: <how it differs by version/platform/deployment>. (evidence: ...)
**Pitfalls**: <approaches that fail, wasted paths, traps>. (evidence: ...)

## Diagnosis
- <What to check first, in what order; what evidence distinguishes the patterns above>.
  (evidence: ...)

## Boundaries & exceptions
- <Where the patterns bend; when to escalate instead>. (evidence: ...)

## References
- <KB articles, docs pages, internal tools cited in resolutions>.

## Related
[[other-topic]] · [[process/stages/relevant-stage]] · [[automation/candidate]]
```

## Automation Candidate Template (`automation/`)

```markdown
---
type: automation-candidate
...
---

# <Candidate name>

**Behavior**: the recurring, rule-like behavior observed. (evidence: ...)
**Determinism**: why this is stable enough to compile down (fixed inputs/outputs, low ambiguity).
**Proposed form**: script | API call | validation rule | routing rule | workflow step.
**Guardrails**: when it must fall back to the worker or a human.
**Regression check**: which golden cases (by ID) must still be handled correctly.
```

## Role OS Template (`role-os.md`)

```markdown
---
title: Role OS
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: role
tags: [...]
exemplars: []
confidence: medium
contested: false
---

# Role OS

## Purpose
What business outcome this Digital Worker supports.

## Role Mission
What the worker is accountable for.

## Process Context
Where this role sits in the process — link the [[process/overview]] stage map.

## Inputs / Outputs
What the worker receives; what it produces (records, decisions, messages, escalations).

## Attention Model
What the worker notices first, ignores, flags, and revisits.

## Evidence Model
What the worker trusts, what must be verified, what is weak signal.

## Decision Model
How the worker chooses its next action — link [[playbooks/decision-framework]].

## Communication Model
How the worker speaks to humans, systems, and managers.

## Authority Boundaries
What the worker may do, may request, must escalate, must never claim.

## Execution Loop
Intake to closure, stage by stage.

## Exception Loop
Novelty, ambiguity, out-of-policy, low-confidence handling.

## Compile-Down Strategy
Which parts of the role should become deterministic automation — link [[automation/]] candidates.

## Self-Extension Policy
How the worker proposes, tests, and governs changes to its own prompts, tools, code, flows, and memory — including how it configures itself for a new domain (e.g. an onboarding interview) and what requires human approval before taking effect.

## Evaluation Model
How good work is measured — link [[evaluations/good-work-criteria]].

## Governance Model
Approvals, rollback, audit, identity, sandboxing, change management.

## Anti-Patterns
How this worker fails.

## Mantra
The compact soul of the role.
```

## Recommended Core Pages

Create these as evidence supports them — never speculatively:

**Process** (see `references/process-model.md`): `process/overview.md`, stage pages, `handoffs.md`, `decision-points.md`, `exceptions.md`.

**Concepts**: `business-object-model.md` (objects, fields, lifecycle), `content-taxonomy.md` (document/content types), `evidence-model.md` (trusted inputs, verification), `exception-patterns.md`; then topic pages as the corpus reveals them.

**Roles**: `roles/persona.md`, `roles/stakeholder-map.md`, `roles/authority-boundaries.md`, `roles/manager-interface.md`.

**Playbooks**: `playbooks/research-method.md`, `playbooks/decision-framework.md`, `playbooks/communication-style.md`.

**Automation**: `automation/automation-candidates.md` (index of candidates), `automation/compile-down-rubric.md`, `automation/deterministic-handoff.md`.

**Governance**: `governance/audit-events.md`, `governance/access-and-identity.md`, `governance/change-management.md`.

**Evaluations**: `evaluations/good-work-criteria.md`, `evaluations/anti-patterns.md`, `evaluations/golden-cases.md` (case-ID references with gists — never trace pages), `evaluations/regression-cases.md`.
