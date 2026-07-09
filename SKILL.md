---
name: digital-worker-grounding
description: "Distill business records and documents into a deep, detailed knowledge wiki — topics, business process, Role OS, automation candidates, governance, evaluations — that grounds a Digital Worker. Extracts rich reusable knowledge with case-ID citations; never turns cases into pages."
version: 2.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [digital-worker, grounding, wiki, knowledge-base, business-process, knowledge-extraction, role-os]
    category: research
    related_skills: [obsidian]
---

# Digital Worker Grounding

Build and maintain a markdown knowledge base that grounds a Digital Worker in how a business actually works.

Cases are fuel, not content. Source records — support cases, CRM objects, tickets, claims, orders, emails, transcripts, SOPs, policies — pass through this skill and leave behind only distilled, reusable knowledge: what the recurring topics are, how the business process flows, how decisions get made, what good work looks like, and what should compile down into deterministic automation. Every durable claim cites the source cases that support it. No case ever becomes a page.

## Hard Rules

These override everything else in this skill and its references.

1. **Never create a page for a single case, record, or document.** Per-case provenance lives in the ingest ledger (one CSV row per case) and in citations on claims — never in pages.
2. **Never create a page or section named after a batch or ingest run.** No `next-2000-patterns.md`, no "Batch 3 update" headings. Knowledge is organized by topic and process, never by when it arrived.
3. **Never write case summaries into the wiki.** Extract the reusable signal and cite the case ID. The one-to-two-line human-readable gist of each case lives in its ledger row, nowhere else. One narrow exception: golden/sentinel references in `evaluations/` may carry a one-line *reason the case is exemplary* (format in `references/provenance.md`).
4. **Depth is the deliverable.** Never write a claim that merely names a taxonomy category ("X is a recurring pattern (evidence: 379 cases)") — category distributions belong in `_meta/` reports, not pages. Every claim carries its substance: the symptom, error signature, cause, step-by-step procedure, criterion, or boundary, detailed enough that a worker could act on a similar case without opening the source (`references/extraction.md`).
5. **Revise pages in place.** New evidence updates existing sentences, deepens existing sections, and bumps evidence counters. Never append parallel per-ingest sections to a page.
6. **Judge by signal-to-noise, not volume.** There is no page budget and no upper limit on wiki size: a 500-page wiki of dense, actionable knowledge is success. **Signal** = anything that helps a worker act on a future case: procedures, error signatures, criteria, variants, pitfalls, references, process facts. **Noise** = case narration, customer identifiers, taxonomy restatements, near-duplicate claims, inert boilerplate, filler prose. Add every piece of signal, however long the wiki gets; add zero noise. The only volume red flags are structural drift: page count approaching case count, or pages organized by case/batch instead of topic (Rules 1–2). Expect **at least** ~50 topic pages per 1,000 heterogeneous cases — fewer means extraction is running shallow.
7. **Every case gets a ledger row** — processed, skipped, or failed. No silent handling.
8. **Orient before writing.** Read `SCHEMA.md`, `index.md`, recent `log.md`, and `_meta/topic-map.md` (if present) before touching any page.
9. **One agent does the ingest.** Never delegate any part of it — reading, classification, extraction, or writes — to subagents.

## When This Skill Activates

Use this skill when the user asks to:

- build, extend, query, or audit a Digital Worker grounding wiki;
- ingest business records, cases, CRM exports, documents, transcripts, SOPs, or other operational evidence;
- distill a corpus into topics, business process documentation, a Role OS, playbooks, automation candidates, governance boundaries, or evaluation criteria.

## Wiki Location

Set via `WIKI_PATH`; default `~/wiki`.

```bash
WIKI="${WIKI_PATH:-$HOME/wiki}"
```

The wiki is plain markdown and must work in Obsidian, VS Code, or any editor.

## Core Principle

Ingestion is distillation:

```text
source cases
  -> classify against taxonomy
  -> novelty gate (does this teach anything new?)
  -> merge reusable knowledge into topic/process/role/automation/governance/evaluation pages
  -> cite case IDs on claims; bump evidence counters
  -> one ledger row per case (classification + gist)
```

Distillation removes the case-specific wrapper, not the knowledge — it maximizes signal-to-noise, never brevity. A topic page should say *more* about its topic than any single case does — symptoms, error signatures, causes, full procedures, variants, pitfalls — because it pools every case's detail. A case counts as "teaching nothing new" only when the wiki already holds **all** of its reusable detail at that depth (the subsumption test in `references/extraction.md`); such cases cost one ledger row and a few counter bumps. That gate exists to prevent *redundancy* (repeating what a page already says is noise), never to limit how much the wiki grows. Matching an existing taxonomy category is never, by itself, grounds to skip extraction — that path produces a histogram of category names, not a knowledge base.

## Architecture

```text
wiki/
├── SCHEMA.md            # domain, conventions, taxonomy, quality rules
├── index.md             # curated catalog of all pages, one-line summaries
├── log.md               # chronological action log
├── role-os.md           # master Digital Worker operating model
├── _meta/               # control plane: ledger, batch state, coverage, reports
│   ├── ingest-ledger.csv
│   ├── pending-categories.md     # parked taxonomy candidates from single-case ingests
│   ├── process-coverage.md       # stage-by-stage evidence table (see references/process-model.md)
│   ├── topic-map.md              # topic → pages map; required once the wiki passes ~75 pages
│   └── batches/<batch-id>/       # state.json + processed-ids.txt + report.md per batch
├── _archive/            # retired pages moved here by lint remedies; never linked from live pages
├── process/             # business process model: stages, handoffs, decisions (first-class)
├── concepts/            # topics: object model, content types, evidence, exceptions
├── roles/               # persona, stakeholder map, authority boundaries
├── playbooks/           # methods, decision frameworks, communication style
├── automation/          # compile-down candidates, deterministic handoffs
├── governance/          # audit, access, approvals, change management
├── evaluations/         # good-work criteria, anti-patterns, golden case refs, regressions
└── queries/             # filed answers worth preserving
```

There is no `raw/` and no `_provenance/` by default: the source system remains the system of record, and the ledger row's `source_ref` + gist is the audit trail. If sources have no system of record (loose files), see `references/provenance.md` for the optional `raw/` escape hatch.

## Operating Modes

### Init — new wiki

1. Determine `WIKI_PATH`; create the directory structure above.
2. Ask the user what business domain/process the wiki grounds.
3. Write `SCHEMA.md` (template in `references/templates.md`), `index.md`, `log.md`.
4. Bootstrap the taxonomy from a stratified sample before any full ingest (`references/batch-ingest.md`).

### Ingest — one case or a corpus

The per-case loop (details and taxonomy axes in `references/extraction.md`):

1. **Read** the case fully: record, related objects, attachments, comments, history. If some artifacts are unavailable (missing attachment binaries, broken links), proceed and record the gap in the ledger `notes`.
2. **Classify** it across the taxonomy axes (case type, topic, process stage, root cause, resolution pattern, actors, systems). Values come from `SCHEMA.md`'s taxonomy; unknowns are written as `unknown:<reason>`, never guessed; new categories are proposed via pending-categories (`references/extraction.md`), never added directly.
3. **Novelty gate** — do the wiki's pages already contain, at full depth, every reusable detail this case exhibits (subsumption test, `references/extraction.md`)?
   - **Yes, fully subsumed**: append the ledger row, bump evidence counters on the claims it confirms. Done. (Category membership alone never qualifies.)
   - **No**: extract every reusable detail — error signatures, causes, procedures, variants, criteria — merge into existing pages (deepening them), create topic pages where warranted, or park a pending category; cite the case ID inline; append the ledger row.
4. **Process check**: if the case reveals a stage, handoff, or decision point the process model lacks, update `process/` pages (`references/process-model.md`).

Every case ends as one row in `_meta/ingest-ledger.csv` (column spec in `references/provenance.md`):

```csv
case_id,source_ref,batch_id,ingested,status,case_type,topic,process_stage,root_cause,resolution_pattern,actors,systems,novel,pages_updated,gist,notes
```

For corpora, follow the batch protocol in `references/batch-ingest.md`: single agent, chunked checkpoints, batch state file, saturation report.

### Query — answer from the wiki

1. Read `index.md` and `_meta/topic-map.md` (if present); search pages for key terms.
2. Answer from durable pages; cite the pages used and their evidence counts.
3. If the synthesis is durable and reusable, file it in `queries/` and add it to `index.md`; append to `log.md`.

### Lint — health and signal-to-noise audit

Run the checks in `references/lint.md`: link/frontmatter/index integrity, the noise detectors (per-case pages, batch-named pages, per-ingest sections, case summaries in pages, structural drift), the shallowness detectors (taxonomy-restatement claims, thin pages under heavy evidence, undocumented substantial topics, worker-test failures), and the saturation audit. Report by severity; append results to `log.md`.

## Completion Criteria (any ingest)

- Every input case has a ledger row (`ok`, `skipped`, or `error`) with classification and gist.
- Every reusable signal extracted either landed in a durable page with case-ID citations or is parked as a pending category (batch state or `_meta/pending-categories.md`).
- Every substantial topic (≥10 cases or ≥5% of the corpus) has a dedicated, detailed page — not just a taxonomy entry.
- Pages pass the **worker test**: a Digital Worker could handle a similar case from the page alone. No page merely restates taxonomy categories with counters.
- No page or section violates the Hard Rules.
- The process model reflects any newly evidenced stages, handoffs, or decision points.
- `index.md`, `log.md`, and — where present — `_meta/topic-map.md` and `_meta/process-coverage.md` are current.
- For batches: `_meta/batches/<batch-id>/report.md` exists with novelty rate and taxonomy changes, and the lint noise + shallowness detectors were run and pass (result recorded in the report).

## References

Load these when performing the corresponding work — they are the authoritative detail:

| File | Load when |
|---|---|
| `references/extraction.md` | classifying cases, extracting signals, deciding page creation vs update |
| `references/batch-ingest.md` | ingesting more than ~10 cases; bootstrapping a taxonomy |
| `references/provenance.md` | writing citations, ledger rows, evidence counters |
| `references/process-model.md` | creating or updating business process pages |
| `references/templates.md` | writing SCHEMA.md, the Role OS, or creating any new page |
| `references/lint.md` | auditing wiki health, noise, or shallow extraction |
