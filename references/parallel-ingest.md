# Parallel Ingest (Optional, Advanced)

Hard Rule 9 in `SKILL.md` sets the default: one agent does the ingest, chunked and checkpointed (`references/batch-ingest.md`). That default exists because parallel writers to shared durable pages produce conflicts, duplication, and taxonomy drift — do not reach for this mode unless the single-agent chunked pipeline is genuinely too slow for the corpus size (tens of thousands of objects or more) and you can commit to the extra discipline below.

If you do parallelize, never let parallel workers freely edit the same durable wiki pages. Parallel *object analysis* is fine; parallel *writes* to shared concept/process pages are not.

## Two-Phase Architecture

```text
batch manifest
  -> per-object subagent analysis
  -> staged extraction + proposed page changes
  -> orchestrator taxonomy merge
  -> serialized wiki writes
  -> per-source audit rows
  -> navigation/log/lint verification
```

- Subagents may read the wiki and source material, and may write per-object trace/staging artifacts under `_meta/ingest-staging/<batch-id>/<source-id>/`.
- Durable pages (`concepts/`, `process/`, `roles/`, `playbooks/`, `automation/`, `governance/`, `evaluations/`, `index.md`) are merged by the orchestrator serially, after reviewing all staged outputs — never written directly by subagents unless pages are pre-assigned and disjoint (page-specialist mode, below).

## Batch Manifest

Before spawning subagents, write `_meta/ingest-staging/<batch-id>/manifest.csv`:

```csv
batch_id,source_id,source_path,source_type,status,assigned_worker,trace_path,staging_path,pages_proposed,pages_modified,error
```

Statuses: `queued`, `analyzing`, `staged`, `merged`, `audited`, `skipped`, `failed`. The manifest is the control plane — every object must end in `audited`, `skipped`, or `failed`.

## Orientation Snapshot

Before parallel work begins, the orchestrator reads `SCHEMA.md`, `index.md`, `_meta/topic-map.md`, recent `log.md`, and the current taxonomy/model pages, then writes a compact `_meta/ingest-staging/<batch-id>/orientation.md` telling subagents the current taxonomy, page-naming conventions, existing canonical pages, and what belongs where.

## Subagent Unit of Work

One subagent per object (or one per small bundle of tiny/strongly-related objects). Give each subagent the source path, the orientation snapshot, related-artifact paths, and instruct it not to create broad batch pages and to classify against the existing taxonomy (`references/extraction.md` axes) before proposing new pages. Require structured output for deterministic merge:

```yaml
source_id: ...
source_path: ...
object_classification: {case_type: ..., topic: ..., process_stage: ..., root_cause: ..., resolution_pattern: ..., actors: [...], systems: [...]}
extracted_signals:
  process: [...] object_model: [...] content_model: [...] evidence: [...]
  decisions: [...] exceptions: [...] communication: [...] automation: [...]
  governance: [...] evaluation: [...]
taxonomy_fit:
  existing_pages_to_update: [...]
  proposed_new_pages: [...]
  uncertain_placements: [...]
proposed_page_changes:
  - page: concepts/example.md
    change_type: append | create | revise
    section: ...
    rationale: ...
    content: ...
    provenance: ...
confidence: high | medium | low
warnings: [...]
```

## Orchestrator Merge Pass

1. Read all staged extraction files.
2. Group proposed changes by target page; de-duplicate overlapping observations.
3. Prefer updating existing canonical pages over creating new ones; create a page only after checking `index.md` and searching existing pages.
4. Resolve naming conflicts and taxonomy drift; merge overlapping proposed-new-pages into the existing page instead of creating a duplicate.
5. If multiple subagents propose changes to the same page: merge into one synthesized section rather than appending repetitive bullets; keep source-specific detail out of the durable page; mark contradictions with confidence and provenance instead of silently choosing one.
6. Apply durable page changes serially; append one audit row per source after its durable changes land.
7. Checkpoint `index.md`, topic map, and `log.md` after each small group for long-running batches (same cadence as `references/batch-ingest.md`).

## Page-Specialist Variant

Use direct subagent writes only when the batch is partitioned by page ownership — e.g. one subagent owns `concepts/content-taxonomy.md`, another owns `automation/automation-candidates.md`. In that mode subagents are page specialists, not object specialists. For object-per-subagent mode, always use staged output + orchestrator merge, never direct writes.

## When to Fall Back

If conflict resolution starts dominating orchestrator time, or the novelty/coverage signal gets noisy across subagents, drop back to the single-agent chunked pipeline in `references/batch-ingest.md`. It is slower per-object but strictly simpler to keep correct, and it is the mode this skill's Hard Rules assume by default.
