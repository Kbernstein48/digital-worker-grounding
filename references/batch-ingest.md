# Batch Ingest Protocol

Single-agent, chunked, resumable. Use this for any corpus larger than ~10 cases. The goal of a batch is distilled knowledge plus a saturation report — not per-case artifacts.

## Overview

```text
bootstrap taxonomy (first batch only, stratified sample)
  -> process cases sequentially in chunks of 25-50
  -> per case: classify -> novelty gate -> merge or counter-bump -> ledger row
  -> checkpoint after each chunk: taxonomy review, noise + depth checks, flush, save state
  -> batch report + log entry
```

**Do not spawn subagents for any part of ingest** — reading, classification, extraction, or writes. One agent performs the entire batch serially (Hard Rule 9). Serialized work is what keeps the taxonomy coherent and the wiki free of duplicates.

**Calibration** — what a healthy batch produces: **at least** ~50 detailed topic pages per 1,000 heterogeneous cases (no upper limit — signal-to-noise governs, not volume), topic pages typically 60–200 lines with symptom/cause/procedure structure, and page depth growing chunk over chunk. A batch that ends with a few dozen skeletal pages has failed at extraction even if every noise check passes.

## Bootstrap (first batch on a new wiki)

Before processing a full corpus, build the initial taxonomy from a **stratified sample** of 30–50 cases. Sample across every stratum visible in the corpus metadata: folder/export group, record type, status, date range, owner/team/region, size (attachment/comment count), and any known escalations. Do not sample randomly alone — random sampling misses the long tail.

From the sample:

1. Draft the taxonomy axes' initial categories into `SCHEMA.md` (mark them `(provisional)` until stabilization).
2. Seed `process/overview.md` with the visible stages (see `references/process-model.md`).
3. Create the needed core pages from the recommended list in `references/templates.md`, plus detailed topic pages for every theme the sample already evidences — each claim cited to sample cases with honest counts and written at full depth (`references/extraction.md`).
4. Write the ledger rows for the sample cases like any other ingest.

Then run the full corpus through the standard loop (skipping already-ledgered sample cases).

## Batch State File

`_meta/batches/<batch-id>/state.json` — the single control-plane artifact, saved at every checkpoint:

```json
{
  "batch_id": "sf-completed-cases-2026-07",
  "source_path": "/path/to/corpus",
  "started": "YYYY-MM-DD",
  "total_sources": 2000,
  "processed_count": 350,
  "processed_ids_file": "processed-ids.txt",
  "novel_count": 41,
  "new_pages": ["concepts/integration-permission-model.md"],
  "pending_counter_bumps": {
    "concepts/oauth-failures.md": {"Expired OAuth client credentials cause 400": 3}
  },
  "pending_categories": [
    {
      "candidate": "proxy-interception",
      "axis": "root_cause",
      "cases": ["00311111", "00322222"],
      "why_existing_fits_fail": "not network-config: transparent proxy rewrites auth headers",
      "importance": "changes required evidence (needs HAR capture)"
    }
  ],
  "contradictions": [],
  "open_questions": [],
  "last_checkpoint": "YYYY-MM-DD chunk 7"
}
```

Keep `processed_ids_file` as a plain-text sibling (one case ID per line) so the JSON stays small. Do NOT mirror per-axis category counts in the state file — every ledger row already carries the full classification, so distributions are computed from `_meta/ingest-ledger.csv` filtered by `batch_id` (a `cut`/`sort | uniq -c` or pandas one-liner) at checkpoints and report time. Resume = read state.json + processed IDs, skip what's done, continue.

## Checkpoint (every 25–50 cases)

1. **Flush**: apply `pending_counter_bumps` to pages (locate each claim by its verbatim text prefix — see `references/provenance.md`); ensure all ledger rows for the chunk are written and list the bumped pages in `pages_updated`.
2. **Pending categories**: promote candidates with ≥3 supporting cases or a passed importance test (`references/extraction.md`) — add to `SCHEMA.md` taxonomy and file their signals. Merge synonyms; reject noise with a recorded reason. Also review `_meta/pending-categories.md` for candidates parked by earlier single-case ingests.
3. **Noise check — mechanical, not self-reported**: list actual new `.md` files since the last checkpoint (inventory diff or `find "$WIKI" -name '*.md' -newer <state.json>` captured before saving state) and reconcile against `new_pages` in the state file. Verify every new page is topic-named — no page counts are policed, only drift: pages named after cases/batches, page count trending toward case count, or near-duplicate pages for the same topic → STOP and consolidate. Spot-check a few edited pages for noise: case narration, customer identifiers, category-restatement claims, duplicated bullets.
4. **Depth audit — the signal floor**: list pages touched this batch with their line counts and cited-case counts. Triggers: any page citing ≥20 cases but under ~40 lines; any claim that names a taxonomy category without substance (Hard Rule 4); any topic-axis category ≥10 cases without a dedicated page; any category >15% share on `topic`/`root_cause`/`resolution_pattern` (≥200 cases in) not yet decomposed. Any trigger → STOP and extract properly before processing more cases — depth debt compounds faster than it repays.
5. **Unknown check**: compute per-axis `unknown`/`other` rates from the ledger; if above ~10% on any single-valued axis (≥50 cases in), stop and refine the taxonomy before the next chunk.
6. **Housekeeping**: update `index.md` for new pages; refresh `_meta/process-coverage.md` (see `references/process-model.md`) and `_meta/topic-map.md` (if present / once the wiki passes ~75 pages); append a checkpoint line to `log.md`; save `state.json`.

### Stabilization

The taxonomy counts as **stabilized** once two consecutive checkpoints pass with no taxonomy changes AND a clean depth audit. After stabilization, growth naturally shifts from new pages to deeper pages, and the `(provisional)` markers come off `SCHEMA.md`. Stabilization is a maturity signal, not a cap — new topics still create new pages whenever the evidence warrants.

## Failure Handling

- Unreadable/malformed case → ledger row with `status=error` and the reason in `notes`; continue.
- Readable case with unavailable pieces (missing attachment binaries, broken related-record links) → `status=ok`, gap recorded in `notes`, and lower confidence on any signal that depended on the missing piece.
- Out-of-scope case (wrong object type, empty record) → `status=skipped` with reason.
- Never let a failure produce a half-written page: finish or revert the page edit before moving on.

## Batch Report

At batch end, write `_meta/batches/<batch-id>/report.md`:

- totals: processed / ok / skipped / error;
- **novelty rate** (novel cases ÷ processed) and its trend across chunks;
- **depth metrics**: page count vs the ≥50/1,000 floor, median/mean topic-page length, the shallow-page list (≥20 cases cited, <40 lines) — must be empty, and cases-per-page for the top 10 topics;
- distribution per taxonomy axis, computed from the ledger (top categories + long tail);
- new pages created, with one-line justification each;
- taxonomy changes: promoted (with supporting case IDs), merged, rejected categories;
- contradictions raised and their pages;
- process-model coverage deltas (stages that gained/lost confidence);
- **lint noise + shallowness detector run and result** (required — the batch is not complete until the critical detectors in `references/lint.md` pass);
- open questions for the user.

Append a summary entry to `log.md`. The batch is complete only when every source has a ledger row, the noise and shallowness detectors pass, and the report exists.

## Saturation

Saturation is the novelty-rate trend **and** the depth audit read together — a low rate only means maturity when pages are deep:

- **Falling toward 10–25% with depth audit passing** — healthy: the wiki is converging; later cases mostly bump counters on rich pages.
- **Low rate with thin pages** — shallow extraction, not saturation (the classic failure: 20% novelty and 30 skeletal pages from 885 cases). The subsumption test is being applied at category level instead of knowledge level; STOP and fix.
- **Flat above ~40% after several hundred cases** — the corpus is more heterogeneous than sampled or the taxonomy is fragmenting; re-run bootstrap sampling on the unprocessed remainder.
- **Near 0% with depth audit passing** — the corpus is exhausted for this wiki; recommend stopping or switching evidence sources rather than grinding through remaining cases.

State the novelty trend and depth metrics explicitly in the batch report and in your summary to the user.
