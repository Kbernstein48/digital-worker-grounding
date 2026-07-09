# Lint: Health and Signal-to-Noise Audit

Run these checks when asked to audit the wiki, after large batches, or when something feels off. Report findings by severity (critical / warning / info) and append the result to `log.md`. The standard throughout is signal-to-noise: wiki size is never a finding by itself — noise and missing signal are.

## Noise Detectors (critical — these violate the Hard Rules)

1. **Per-case pages**: any page whose subject is a single case/record — named after a case ID, or citing exactly one case **while reading as a case narrative** (names, dates, ticket flow) rather than stating a reusable pattern. Carve-out: pages with `rare-but-important: true` frontmatter (importance test, `references/extraction.md`) and structural bootstrap/process pages legitimately cite one case — check that they state patterns, not stories.
2. **Batch-named pages**: any file or heading **outside `_meta/`** containing batch/run identifiers (`batch`, `next-2000`, `first-100`, run dates used as topic names). Companion check: batch artifacts (state.json, processed-ids.txt, report.md) exist only under `_meta/batches/`.
3. **Per-ingest sections**: headings like "… batch update", "New evidence from …", or repeated near-duplicate bullets appended over time instead of revised claims.
4. **Case summaries in pages**: paragraphs that narrate one case's story rather than stating a reusable pattern with citations. Carve-out: one-line golden/sentinel *reasons* in `evaluations/` pages (the Hard Rule 3 exception — they must state what the case demonstrates and point to the ledger, not retell it).
5. **Structural drift**: page count trending toward case count, near-duplicate pages for the same topic, or one directory holding the overwhelming majority of all pages. High page counts alone are not a finding — pages organized by case or batch instead of topic are.

Remedy for 1–4: extract any reusable claim into the proper topic/process page with citations, ensure the ledger rows exist, then move the offending page to `_archive/` (or delete it) and update `index.md`.

## Shallowness Detectors (critical — these violate Hard Rule 4)

6. **Taxonomy-restatement claims**: any claim whose substance is only a category name and a counter — "`documented-solution` is a recurrent completion pattern. (evidence: 379 cases)". Category distributions belong in `_meta/` reports.
7. **Thin pages under heavy evidence**: any page citing ≥20 cases but under ~40 lines — that many cases cannot yield that little knowledge; extraction skipped the content.
8. **Undocumented substantial topics**: any `topic`-axis category with ≥10 ledger cases and no dedicated page, any category >15% share on `topic`/`root_cause`/`resolution_pattern` (≥200 cases in) that has not been decomposed, or a wiki dramatically under the ≥50 topic pages per 1,000 heterogeneous cases floor.
9. **Worker-test failures**: sample 3–5 ledger cases and check whether the pages covering their topics would let a Digital Worker handle a similar case — symptoms, causes, step-by-step resolutions present, not just labels.

Remedy for 6–9: re-open the cited cases via the ledger (`pages_updated` / topic filters) and extract the missing depth into the pages — symptoms, error signatures, causes, procedures, variants — per `references/extraction.md`. This is the one remedy that adds text rather than removing it.

## Integrity Checks (warning)

- Broken `[[wikilinks]]` and links to `_archive/` pages.
- Orphan pages: durable pages linked from nowhere and absent from `index.md`.
- `index.md` completeness: every durable page listed exactly once, one-line summary present.
- Frontmatter: missing/invalid fields, `type` not in the list defined in `references/provenance.md`, tags not in `SCHEMA.md` taxonomy. (`SCHEMA.md`, `index.md`, and `log.md` are exempt — they carry no frontmatter.)
- Claims without citations: bullet-point claims lacking `(evidence: …)` markers.
- Stale counters: claim counters that disagree with a ledger recount for that page — filter ledger `pages_updated` by the page path; this works because counter-bump rows list the page too (`references/provenance.md`).
- Pages over ~200 lines that should split by topic.
- `⚠ contested` claims or `contested: true` pages older than a month without a resolution note.

## Ledger Checks (warning)

- Rows with `status=error`/`skipped` lacking a reason in `notes`.
- Rows with `novel=yes` but empty `pages_updated` (novel signals must be filed; parked-only cases are recorded as `novel=no` with a `pending:<candidate>` note — flag `novel=no` pending rows only if the referenced candidate appears nowhere in `_meta/pending-categories.md` or any batch state file).
- Stale pending candidates: entries in `_meta/pending-categories.md` untouched across two or more subsequent ingests (info-level — surface them for promotion or rejection).
- `unknown:*` or `other` above ~10% on any single-valued axis (taxonomy debt; waived below 50 total cases).
- Gists containing emails, phone numbers, or credential-like strings (sanitization failure).
- Cases listed in a batch's processed-ids file (state.json `processed_ids_file`) but missing from the ledger, or vice versa.
- `raw/` discipline: `raw/` may exist only when ledger `source_ref` values point into it; it must contain no authored `.md` pages; flag any `raw/` growth from a batch whose sources have a system of record.

## Saturation & Coverage (info)

- Novelty-rate trend across recent batches (from batch reports): rising novelty in a mature wiki suggests taxonomy fragmentation; near-zero suggests the evidence source is exhausted.
- `_meta/process-coverage.md` dark stages: process stages with thin or no evidence.
- Taxonomy axes whose category distribution is one giant bucket (under-split) or a long tail of single-case categories (over-split).
- `log.md` / `_meta/topic-map.md` staleness versus recent ledger activity.

## Output

```markdown
## [YYYY-MM-DD] lint | <scope>
- Critical: <n> (list)
- Warning: <n> (list)
- Info: <n> (list)
- Recommended actions: ...
```

Fix critical findings immediately when authorized; otherwise present them to the user with the remedy for each.
