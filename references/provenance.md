# Provenance: Citations, Ledger, and Evidence Counters

Provenance in this skill is **citation-based, not page-based**. The source system (Salesforce, ServiceNow, a document repository) remains the system of record. The wiki stores pointers and a one-line gist per case — never case content.

## Inline Citations

Every durable claim carries a visible citation with up to 3 exemplar case IDs and a running total:

```markdown
- Expired OAuth client credentials cause 400 errors on token refresh; rotating the
  secret in the external app registration resolves it. (evidence: 14 cases — e.g. 00123456, 00234871)
```

Rules:

- Cite at the **claim level**, not the page level. A page with ten claims has ten citations. A multi-line claim-block (a pattern's symptom/cause/resolution, a numbered procedure) carries one citation per block or per labeled part — not per line.
- Verbatim error signatures, commands, and config keys inside claims are reusable knowledge, not case detail — keep them exact, sanitize customer identifiers, and use `<placeholders>` for instance-specific values.
- A brand-new claim is born as `(evidence: 1 case — e.g. <ID>)`.
- Exemplars should be the clearest instances, not the first seen. Swap in a better exemplar when one appears.
- Use the **human-facing case number** (the one a person would quote, e.g. `02900242`) in citations and in the ledger `case_id`; opaque record IDs belong in `source_ref`.
- The full claim→cases mapping is NOT stored in the page. It is recoverable from the ledger: filter `pages_updated` by this page's path (which is why counter-bump rows must list the page — see below).

## Evidence Counters

When a non-novel case confirms an existing claim, bump its counter in place and list the page in that case's ledger `pages_updated`:

```markdown
(evidence: 14 cases — e.g. 00123456, 00234871)
→ (evidence: 15 cases — e.g. 00123456, 00234871)
```

- If a confirmed claim has no `(evidence: …)` marker yet (older prose, template boilerplate), add one on first confirmation, counting this case plus any case IDs already cited in the claim text.
- **Claim addressing**: when deferring bumps during a batch (`pending_counter_bumps` in the state file), key each bump by page path plus a **verbatim prefix of the claim's bullet text** long enough to grep uniquely — never an invented anchor. Example: `{"concepts/oauth-failures.md": {"Expired OAuth client credentials cause 400": 3}}`.
- During batch ingest, bumps may be accumulated in the state file and flushed at checkpoints instead of editing the page per case — but pages and ledger must agree by the end of the batch.

## Page Frontmatter

```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: topic | process | object-model | content-model | decision-framework | playbook |
      role | automation-candidate | governance | evaluation | anti-pattern | query
tags: [from SCHEMA.md taxonomy]
exemplars: [up to 5 case IDs that best represent this page's subject]
confidence: high | medium | low
contested: false
rare-but-important: false   # true only for single-case pages passing the importance test (references/extraction.md)
---
```

`exemplars` is a curated shortlist for the whole page; claim-level citations remain in the body. `role-os.md` uses `type: role`. `SCHEMA.md`, `index.md`, and `log.md` are control files and carry no frontmatter.

## SQLite Knowledge Database

Maintain `_meta/knowledge.db` alongside the CSV ledger for machine-readable provenance and review workflows. The database is an index, not a replacement for the markdown wiki or the source system: pages remain the human-facing knowledge base, Salesforce/other source systems remain the record of truth, and the DB makes the evidence inspectable.

Required core tables:

```sql
CREATE TABLE cases (
  case_id TEXT PRIMARY KEY,
  source_ref TEXT,
  batch_id TEXT,
  ingested TEXT,
  status TEXT,
  case_type TEXT,
  topic TEXT,
  process_stage TEXT,
  root_cause TEXT,
  resolution_pattern TEXT,
  actors TEXT,
  systems TEXT,
  novel TEXT,
  pages_updated TEXT,
  gist TEXT,
  notes TEXT
);

CREATE TABLE pages (
  page_path TEXT PRIMARY KEY,
  title TEXT,
  type TEXT,
  updated TEXT,
  line_count INTEGER
);

CREATE TABLE claims (
  claim_id TEXT PRIMARY KEY,
  page_path TEXT NOT NULL,
  heading TEXT,
  claim_text TEXT NOT NULL,
  evidence_count INTEGER,
  exemplar_case_ids TEXT,
  claim_kind TEXT,
  FOREIGN KEY(page_path) REFERENCES pages(page_path)
);

CREATE TABLE claim_cases (
  claim_id TEXT NOT NULL,
  case_id TEXT NOT NULL,
  support_type TEXT DEFAULT 'exemplar',
  PRIMARY KEY (claim_id, case_id),
  FOREIGN KEY(claim_id) REFERENCES claims(claim_id),
  FOREIGN KEY(case_id) REFERENCES cases(case_id)
);

CREATE TABLE data_points (
  data_point_id TEXT PRIMARY KEY,
  case_id TEXT NOT NULL,
  page_path TEXT,
  data_type TEXT NOT NULL,
  normalized_text TEXT NOT NULL,
  source_field TEXT,
  source_artifact TEXT,
  confidence TEXT DEFAULT 'medium',
  promoted_to_claim_id TEXT,
  FOREIGN KEY(case_id) REFERENCES cases(case_id),
  FOREIGN KEY(page_path) REFERENCES pages(page_path),
  FOREIGN KEY(promoted_to_claim_id) REFERENCES claims(claim_id)
);

CREATE INDEX idx_data_points_case ON data_points(case_id);
CREATE INDEX idx_data_points_type ON data_points(data_type);
CREATE INDEX idx_claims_page ON claims(page_path);
```

Populate or refresh `_meta/knowledge.db` after every batch checkpoint and after substantial rewrites. At minimum, load every ledger row into `cases`, every durable markdown page into `pages`, every cited claim into `claims`, exemplar links into `claim_cases`, and extracted reusable observations into `data_points` (errors, commands, config keys, versions, decisions, supportability boundaries, evidence gaps). Do not store raw customer narratives or source documents in the DB; `normalized_text` should be sanitized and reusable in the same way wiki claims are.

This pattern is generic for any source business object. The table name `cases` is retained for compatibility with existing wikis, but a row may represent any ingested business record: support case, incident, claim, opportunity, order, invoice, application, transcript, call, document, or other object. Use the human-facing record identifier in `case_id`, describe the source in `source_ref`, and adapt `case_type`, `topic`, `process_stage`, `root_cause`, `resolution_pattern`, `actors`, and `systems` to the domain taxonomy in `SCHEMA.md`. When a corpus does not naturally have "cases", treat `cases` as the canonical `records` table for the wiki.

## Query Tool

Use `scripts/query_knowledge_db.py` to inspect `_meta/knowledge.db` instead of writing ad hoc SQL for routine review. The tool uses generic business-object language (`record`) while reading the compatibility table `cases` underneath.

Examples:

```bash
python scripts/query_knowledge_db.py --wiki /path/to/wiki counts
python scripts/query_knowledge_db.py --wiki /path/to/wiki top --by data_type
python scripts/query_knowledge_db.py --wiki /path/to/wiki search "trustServerCertificate"
python scripts/query_knowledge_db.py --wiki /path/to/wiki record 02900242
python scripts/query_knowledge_db.py --wiki /path/to/wiki records --topic upgrade --system "Automation Suite"
python scripts/query_knowledge_db.py --wiki /path/to/wiki page concepts/sql-database-connectivity.md
python scripts/query_knowledge_db.py --wiki /path/to/wiki data-points --type error_or_boundary --limit 20
python scripts/query_knowledge_db.py --wiki /path/to/wiki claims --page concepts/upgrade-readiness.md
python scripts/query_knowledge_db.py --wiki /path/to/wiki sql "SELECT data_type, COUNT(*) FROM data_points GROUP BY data_type"
```

The `sql` subcommand is read-only by design. Use it for analysis and audit queries; use the batch/refresh script to rebuild the DB after wiki changes.

## The Ingest Ledger

`_meta/ingest-ledger.csv` — append-only, one row per case ever ingested. This file replaces per-case trace pages entirely.

```csv
case_id,source_ref,batch_id,ingested,status,case_type,topic,process_stage,root_cause,resolution_pattern,actors,systems,novel,pages_updated,gist,notes
```

| Column | Content |
|---|---|
| `case_id` | The human-facing case number in the source system |
| `source_ref` | How to reach the original. Preference order: resolvable URL; else `<system>:<record-id>` (e.g. `salesforce:500Pa00001Jom1HIAR`) optionally followed by the export file path; else the file path alone for loose documents |
| `batch_id` | Batch identifier, or `single` for one-off ingests |
| `ingested` | YYYY-MM-DD |
| `status` | `ok` \| `skipped` \| `error` — skips/errors must say why in `notes`. Partially readable cases (e.g. missing attachment binaries) stay `ok` with the gap noted in `notes` |
| `case_type` … `systems` | Classification per axis; `none` or `unknown:<reason>` where applicable; multi-values separated by `;` |
| `novel` | `yes` \| `no` — did it pass the novelty gate. Pending-category-only cases are `no` with a `pending:<candidate>` note (see `references/extraction.md`) |
| `pages_updated` | `;`-separated wiki paths this case touched — including pages whose only change was a counter bump. Empty only for parked/skipped/error rows |
| `gist` | 1–2 line human-readable summary of the case — the ONLY place a per-case summary exists. Quote it; no newlines; no emails/PII |
| `notes` | errors, skip reasons, unavailable artifacts, contradictions raised, `pending:<candidate>` references |

The ledger answers every audit question the old trace pages answered: what was this case about, what did we learn from it, which pages did it feed, and where do I read the original.

### Sanitization

Gists and notes must not contain email addresses, phone numbers, credentials, or customer-identifying strings beyond the case ID itself. Strip email-header boilerplate. The case ID is the pointer; the source system holds the sensitive detail.

## Golden and Sentinel Cases

Evaluations reference cases by ID plus a one-line **reason the case is exemplary** — a statement about what it demonstrates, not a retelling of what happened (the gist stays in the ledger):

```markdown
## Golden cases
- **00123456** — demonstrates: complete evidence checklist gathered before any action
  on an integration-permission failure. (gist and source_ref: ledger)
```

This is the sanctioned exception in Hard Rule 3, and it applies only inside `evaluations/` pages. Mark sentinel cases (first/best/contradictory example of a category) in the ledger `notes` and reference them the same way from taxonomy and evaluation pages.

## Escape Hatch: Loose Sources

If a corpus has no system of record (e.g. a folder of PDFs someone emailed), you may create `raw/` and copy sources there so `source_ref` has something durable to point at. `raw/` is immutable — read it, never edit it; it holds source files only, never authored pages. This is the only circumstance in which the wiki stores source material, and lint verifies it stays that way.
