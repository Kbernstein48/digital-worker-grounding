# Business Process Model

The business process is a first-class deliverable of this skill, not a by-product. A Digital Worker cannot be grounded in *what* the topics are without knowing *where in the flow of work* it is acting. Every ingested case maps to a process stage; the process model accumulates evidence like any other knowledge.

## Required Pages

```text
process/
├── overview.md          # end-to-end stage map: triggers, stages, exits
├── stages/<stage>.md    # one page per major stage
├── handoffs.md          # transitions between actors/teams/systems
├── decision-points.md   # where the flow branches and on what criteria
└── exceptions.md        # paths off the happy path: escalations, reopens, rework
```

Derive stage names from evidence, not from an assumed template. If the corpus shows `intake → triage → investigation → resolution → closure`, use those; if the real process differs, document the real one.

These pages are **structural**: they are exempt from the recurring-cases page-creation criterion (`references/extraction.md`) and may be created from bootstrap-sample or single-case evidence. Seed `overview.md` during bootstrap (or on the first ingest of a new wiki); split out stage pages and the handoffs/decision-points/exceptions pages as evidence accumulates — single-case process evidence goes into `overview.md` with an `(evidence: 1 case — …)` citation until then. Honest per-claim counts are what keep thin evidence from masquerading as established process.

## overview.md

- The stage map as a list or Mermaid diagram: trigger → stages → exit states.
- One line per stage: purpose, primary actor, typical duration if evidenced.
- Entry points (how work arrives) and exit states (all the ways work ends, including abandonment).
- Citations: each stage claim carries case evidence like any other claim.

## Stage Pages (`process/stages/<stage>.md`)

For each stage, as evidence supports it — at the same depth standard as topic pages (`references/extraction.md`): concrete activities, criteria, and checks a worker could follow, not stage names with counters:

- **Entry criteria** — what must be true for work to arrive here.
- **Actors** — who/what performs the stage; who is accountable.
- **Work performed** — the actual activities in order: what gets read, checked, produced, and verified, linked to relevant `playbooks/` and `concepts/` pages.
- **Evidence used** — inputs consulted; link to the evidence model.
- **Decisions** — branch points inside the stage; link to `process/decision-points.md`.
- **Exit criteria & handoffs** — where work goes next and what transfers with it.
- **Exceptions** — how this stage goes wrong; link to `process/exceptions.md`.
- **Timing/SLA signals** — if the corpus evidences them.

## Mapping Cases to Stages During Ingest

Every ledger row records `process_stage` — the stage where the case's *meaningful work* happened (a support case may traverse all stages; record the stage(s) that the case's evidence actually illuminates, `;`-separated).

A case updates the process model when it evidences:

- a stage, entry point, or exit state not yet documented;
- a handoff not yet documented, or one that contradicts the documented flow;
- a decision point, its criteria, or a new branch;
- an exception path (escalation trigger, reopen loop, rework cycle);
- actor/ownership facts that differ from the documented model.

## Process Coverage

Maintain `_meta/process-coverage.md` — a small table, refreshed at every batch checkpoint (housekeeping step 5 in `references/batch-ingest.md`):

```markdown
| Stage | Evidence (cases) | Confidence | Known gaps |
|---|---|---|---|
| intake | 412 | high | weekend routing unclear |
| triage | 380 | high | — |
| escalation | 9 | low | exit criteria unevidenced |
```

Rules:

- Stages with thin evidence are **dark stages** — call them out in batch reports and recommend evidence sources that would illuminate them (different record types, logs, interviews).
- `process_stage = unknown:*` ledger rows feed this table: a rising unknown rate means the stage model doesn't match reality — revise the model rather than forcing cases into it.
- Coverage is about the *model's* trustworthiness, not completionism: 9 cases may be plenty for a simple stage; 400 may be too few for a complex one. Note confidence, not just counts.
