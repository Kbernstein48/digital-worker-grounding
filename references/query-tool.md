# Knowledge DB Query and Review Tools

The grounding wiki includes a generic SQLite query helper plus review/maintenance tools. Use these for business-object corpora of any kind; `record` means the ingested source object (case, ticket, claim, order, invoice, document, transcript, etc.).

## Maintenance and Review Scripts

```bash
# Rebuild _meta/knowledge.db from ledger, pages, and source records
python scripts/refresh_knowledge_db.py --wiki "$WIKI"

# Check claims, citations, data points, orphan records, and weak evidence
python scripts/evidence_audit.py --wiki "$WIKI"

# Review one wiki page: claims, supporting records, gaps, split/merge hints
python scripts/page_review.py --wiki "$WIKI" concepts/<topic>.md

# Inspect one source business record and its wiki contribution
python scripts/record_inspector.py --wiki "$WIKI" <record-id>

# Find data points that should be promoted into durable article claims
python scripts/promote_data_points.py --wiki "$WIKI" --page concepts/<topic>.md

# Enforce article quality: no snippets, case summaries, raw email, or shallow pages
python scripts/article_quality_lint.py --wiki "$WIKI" --write-report

# Discover recurring topics/errors/configs that may deserve new pages
python scripts/topic_discovery.py --wiki "$WIKI" --min-records 3

# Extract exact errors, commands, config keys, versions, and paths into signatures
python scripts/extract_signatures.py --wiki "$WIKI"

# Check supportability/procedure claims against docs via `uip docsai ask`
python scripts/docs_grounding_check.py --wiki "$WIKI" --page concepts/<topic>.md

# Parse attachments/content into sanitized data points and artifact records
python scripts/attachment_ingest.py --wiki "$WIKI" --source /path/to/source
```

The tools are intended to be chained: refresh DB → audit/lint → page/record review → promote data points/topic discovery → rewrite pages → refresh DB again.

## Query Helper

The grounding wiki includes a generic SQLite query helper:

```bash
python <skill-dir>/scripts/query_knowledge_db.py --wiki "$WIKI" <command>
```

The tool is generic over business-object corpora. The current schema retains the table name `cases` for historical support-case corpora, but the CLI uses `record`/`records` language and applies equally to tickets, claims, orders, opportunities, emails, documents, or any other indexed business object.

## Commands

```bash
# Show tables/views and columns
python scripts/query_knowledge_db.py --wiki "$WIKI" schema

# Show row counts for every table
python scripts/query_knowledge_db.py --wiki "$WIKI" counts

# Run read-only SQL. Only single SELECT/WITH or safe PRAGMA statements are allowed.
python scripts/query_knowledge_db.py --wiki "$WIKI" sql "SELECT data_type, COUNT(*) FROM data_points GROUP BY data_type"

# Show one source record by business-facing ID
python scripts/query_knowledge_db.py --wiki "$WIKI" record 02885530

# Filter records by topic/system/status/free text
python scripts/query_knowledge_db.py --wiki "$WIKI" records --topic upgrade --system "Automation Suite" --limit 20

# Show page metadata plus claim/data-point counts
python scripts/query_knowledge_db.py --wiki "$WIKI" page concepts/sql-database-connectivity.md

# Filter durable wiki claims
python scripts/query_knowledge_db.py --wiki "$WIKI" claims --page sql --term trustServerCertificate --limit 20

# Filter extracted reusable data points
python scripts/query_knowledge_db.py --wiki "$WIKI" data-points --type error_or_boundary --term PKIX --limit 20

# Search records, claims, and data points together
python scripts/query_knowledge_db.py --wiki "$WIKI" search uipathctl --limit 20

# Common summaries
python scripts/query_knowledge_db.py --wiki "$WIKI" top --by data_type
python scripts/query_knowledge_db.py --wiki "$WIKI" top --by page_claims
python scripts/query_knowledge_db.py --wiki "$WIKI" top --by page_data_points
python scripts/query_knowledge_db.py --wiki "$WIKI" top --by topics
```

## Output Formats

Use `--format table` (default), `--format json`, or `--format csv`:

```bash
python scripts/query_knowledge_db.py --wiki "$WIKI" --format json data-points --term "multi subnet failover"
```

## Safety Rules

- The tool is read-only. The `sql` command refuses anything except one `SELECT`/`WITH` statement or safe schema PRAGMAs.
- Query results may include sanitized source-derived text. Do not paste raw customer narratives into wiki pages; convert results into reusable operational claims and cite the source record IDs.
- If a query result exposes an unsanitized secret, credential, email, phone number, or customer identifier, treat it as a sanitization bug: redact it in the source-derived index before using it.

## When to Use

Use this tool before answering corpus-level questions such as:

- Which records support this topic?
- Which pages have the most cited claims?
- What reusable data points mention a command, error, config key, product, or boundary?
- Which source records updated a page?
- Which topics have evidence but weak article coverage?
- Which extracted data points should be promoted into article claims?
