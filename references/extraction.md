# Extraction: Classification, Depth, Novelty Gate, and Page Decisions

This is the authoritative guide for turning one case into wiki knowledge. It assumes the Hard Rules in `SKILL.md`. The output standard throughout is the **worker test**: could a Digital Worker, reading only the wiki page, handle a similar case end to end? If not, extraction is incomplete.

## Taxonomy Axes

Classify every case across these axes. Values come from `SCHEMA.md`'s taxonomy; the taxonomy grows through the pending-categories process (below), never ad hoc.

| Axis | Question |
|---|---|
| `case_type` | What kind of work item is this? (e.g. how-to, defect, config issue, licensing, escalation) |
| `topic` | What subject/product/component area is it about? This is the **largest axis** — expect dozens of categories on a big corpus, each specific enough to name a real page (`orchestrator-certificate-renewal`, not `technical-issue`) |
| `process_stage` | Where in the business process did the meaningful work happen? |
| `root_cause` | Why did the underlying situation occur? |
| `resolution_pattern` | How was it resolved? (e.g. config fix, documentation pointer, hotfix, workaround, no-fault closure) |
| `actors` | Which roles/teams/systems acted? |
| `systems` | Which products, tools, or integrations were involved? |

Rules:

- If an axis does not apply, write `none`. If you cannot classify, write `unknown:<short reason>` — unknowns must survive into the ledger; they are taxonomy debt, not noise.
- Once ≥50 cases are ingested: if `unknown`/`other`/`misc` exceeds ~10% on any of `case_type`, `topic`, `process_stage`, `root_cause`, or `resolution_pattern`, stop and refine the taxonomy. (`actors`/`systems` are exempt; the rule is waived below 50 cases — normal cold start.)
- **Over-broad category rule**: once ≥200 cases are in, any single category holding >15% of cases on the `topic`, `root_cause`, or `resolution_pattern` axis must be decomposed into subcategories (via pending-categories, reviewed at the next checkpoint). A 300-case `install-upgrade` bucket is not a category — it is a subcorpus hiding dozens of topics.

**Classification is routing, not extraction.** The category tells you *which page* the case's knowledge belongs on; it says nothing about *what* to write there. A case is never "done" because it was classified.

## Cold Start (no taxonomy yet)

- **Corpus available (≥ ~30 cases)**: run the stratified-sample bootstrap in `references/batch-ingest.md`.
- **Single case or tiny corpus**: seed a **provisional taxonomy** directly into `SCHEMA.md` — one or two categories per axis, marked `(provisional)`. This is the sanctioned exception to "never ad hoc"; revisit every provisional category once ~50 cases are in the ledger.

## Depth of Extraction

From every non-subsumed case, capture ALL reusable detail. Reusable means it would help on a *similar future case* — which includes, and sanitization aside is not limited to:

- **Verbatim error signatures** — exact error messages, codes, log lines, stack-trace heads. These are reusable knowledge (a worker greps for them), not case detail. Strip customer identifiers, keep the technical text.
- **Exact products, components, versions** — "Automation Suite 2023.10 on OpenShift" teaches; "the product" doesn't.
- **Step-by-step procedures** — the actual resolution sequence: commands, config keys, UI paths, order of operations, verification steps. Generalize names/paths with `<placeholders>`, never drop the steps.
- **Preconditions and environment factors** — OS/versions/network/permissions under which the problem occurs or the fix applies.
- **Decision criteria** — what the handler checked to choose between options, and what evidence tipped it.
- **Variants and boundaries** — how the pattern differs by version, platform, or deployment; where the standard fix does NOT work.
- **Pitfalls and dead ends** — approaches that were tried and failed (these prevent repeated waste).
- **References** — KB articles, docs pages, internal tools cited in the resolution.
- **Communication moves** — sanitized phrasing patterns for asks, expectation-setting, escalation (→ `playbooks/`).

What this looks like on a page — the difference between a histogram and knowledge:

```markdown
BAD (taxonomy restatement — violates Hard Rule 4):
- `documented-solution` is a recurrent completion pattern. (evidence: 379 cases)

GOOD (a claim a worker can act on):
### Robot service fails to start after OS patching
**Symptom**: `UiPath Robot` service stops seconds after start; Event Viewer shows
`System.IO.FileLoadException: Could not load file or assembly 'UiPath.Service.Host'`.
(evidence: 9 cases — e.g. 02871234, 02883456)
**Cause**: the OS patch rolled back the .NET runtime the service targets. (evidence: 7 cases)
**Resolution**:
1. `dotnet --list-runtimes` — confirm the runtime version the service requires is missing.
2. Reinstall the runtime bundle shipped with the Robot MSI (`<install-media>\Runtime\`).
3. Restart the service; verify the robot shows Connected in Orchestrator.
(evidence: 9 cases)
**Variant**: on Windows Server 2016 the rollback also resets service recovery options —
re-apply them or the failure looks intermittent. (evidence: 2 cases)
```

Sections and multi-line procedures carry one citation per claim-block, not per line (`references/provenance.md`).

## Signal Categories

Signals map to wiki layers:

- **Process** — triggers, stage transitions, handoffs, approvals, timing → `process/`
- **Object/content model** — object types, fields, relationships, document structures → `concepts/`. **Relevance filter**: document only fields that bear on the work; recurring-but-inert platform plumbing is listed once as "ignored fields" and never accumulates evidence.
- **Evidence** — inputs required, trusted, verified, commonly missing → `concepts/` + `playbooks/`
- **Decisions** — decision points, criteria, branches → `playbooks/` + `process/`
- **Exceptions** — blockers, ambiguity, out-of-policy, escalation triggers → `concepts/` + `process/`
- **Communication** — asks, recaps, stakeholder language → `playbooks/`
- **Automation** — deterministic checks, extractors, validators, routing rules → `automation/`
- **Governance** — authority, approvals, audit, access, compliance → `governance/`
- **Evaluation** — good/bad handling, regression-worthy scenarios → `evaluations/`

## The Novelty Gate (subsumption test)

The gate is a **redundancy filter, not a volume limiter**: its only job is to keep the wiki from saying the same thing twice (repetition is noise). It never suppresses new signal, however large the wiki grows.

A case is **fully subsumed** — ledger row + counter bumps only — when existing pages already contain **every** reusable detail the case exhibits, at the depth defined above: its error signature is documented, its cause is explained, its resolution steps are written, its environment variant is covered, and its process path is mapped. Check the case's *content* against the page's *sections*; matching a taxonomy category is never confirmation.

If the case adds **anything** — a new symptom presentation, an unlisted version behavior, an extra resolution step, a sharper decision criterion, a failed approach, a contradiction, a boundary — that detail gets extracted, however familiar the category. Cases like this are `novel: yes` even when no new page results.

A case whose *only* contribution is a candidate taxonomy category is `novel: no` with a `pending:<candidate>` ledger note; it counts as novel when the category is promoted.

Expected trajectory: early ingest runs high (most cases deepen pages); a genuinely mature wiki settles lower as pages saturate. Rates are diagnostics, never targets — there is no prize for a low novelty rate. **A low novelty rate with thin pages is not maturity — it is shallow extraction** (the pilot failure: 20% novelty, 30 skeletal pages from 885 cases). Judge saturation by novelty rate AND the depth audit together (`references/batch-ingest.md`).

## Filing a Novel Signal

Priority order:

1. **Deepen an existing claim/section** — add the variant, step, signature, or criterion where it belongs; sharpen wording; note contradictions.
2. **Add a claim-block to an existing page** — a first-sighting block is legal at `(evidence: 1 case — e.g. <ID>)`.
3. **Create a new topic page** — see criteria below. Depth pressure is a valid creation reason: when a topic's section on a shared page needs symptom/cause/resolution structure of its own, split it out.
4. **Park it** — no suitable page and creation criteria unmet → pending category. Parked signals satisfy completion; they are pending, not lost.

Contradictions: keep both statements, each cited and dated; mark the claim line `⚠ contested`; page-level `contested: true` only when the central claim is disputed; flag in log/batch report. Never silently overwrite.

### Page-Creation Criteria

Create a new page when:

- The topic is **recurring** (≥3 cases), **substantial** (any topic-axis category with ≥10 cases *must* have its own page), or **rare-but-important** (novelty gate importance: changes worker action, routing, evidence, authority, risk, or automation feasibility — set `rare-but-important: true` in frontmatter).
- It has a stable, topic-based name a Digital Worker would search for.
- It is not: a person, customer, one-off name, record ID, email header, or incidental string — and not a case or batch.

Prefer specific pages over mega-pages: `automation-suite-upgrade-issues.md` at 180 detailed lines beats an `install-upgrade.md` at 400. Split past ~200 lines by subtopic. New pages join `index.md`, tagged per `SCHEMA.md`, in the same edit.

Structural exception: `process/` Required Pages and bootstrap core pages may be created from single-case or sample evidence with honest counts (`references/process-model.md`).

### Pending Categories (taxonomy growth)

Record candidates with axis, supporting case IDs, why existing categories don't fit, and why it matters — in the batch state's `pending_categories`, or `_meta/pending-categories.md` for single-case ingests (reviewed at every future ingest and lint). Promote at ≥3 cases or on the importance test; record rejections with reasons.

## What Goes Where (the abstraction rule)

| Observation | Destination |
|---|---|
| Identifies the customer or narrates this case's timeline | Ledger row `gist` — nowhere else |
| Error signature, procedure, config detail that would recur | Topic page in `concepts/` — verbatim, sanitized, cited |
| Recurring process/content/object pattern | `concepts/` or `process/` page, cited |
| Teaches how the worker should act | `role-os.md`, `roles/`, `playbooks/` |
| Stable and rule-like | `automation/` candidate |
| Touches permission, risk, audit, identity | `governance/` |
| Defines good/bad handling | `evaluations/` (criteria + golden case-ID references) |
| New but unfiled (no home, thresholds unmet) | Pending category |
