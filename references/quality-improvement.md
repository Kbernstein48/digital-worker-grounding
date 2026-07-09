# Quality Improvement Pass

Use this when a wiki already exists and the user asks to improve quality, deepen articles, remove noise, or make pages read like real wiki articles.

## Required tool chain

1. Refresh the DB first:
   ```bash
   python scripts/refresh_knowledge_db.py --wiki "$WIKI"
   ```
2. Run audits before editing:
   ```bash
   python scripts/evidence_audit.py --wiki "$WIKI"
   python scripts/article_quality_lint.py --wiki "$WIKI" --write-report
   python scripts/topic_discovery.py --wiki "$WIKI" --min-records 3
   ```
3. Review the weakest pages directly:
   ```bash
   python scripts/page_review.py --wiki "$WIKI" <page.md>
   python scripts/promote_data_points.py --wiki "$WIKI" --page <page.md>
   python scripts/record_inspector.py --wiki "$WIKI" <record-id>
   ```
4. Edit pages in place. Promote repeated data points into durable claims. Remove snippets, source-thread prose, customer/person identifiers, scheduling chatter, and case-summary language. Split topics only when evidence supports a reusable topic.
5. Refresh and verify again:
   ```bash
   python scripts/refresh_knowledge_db.py --wiki "$WIKI"
   python scripts/article_quality_lint.py --wiki "$WIKI"
   python scripts/evidence_audit.py --wiki "$WIKI"
   ```
6. Update `index.md`, `_meta/topic-map.md`, `log.md`, and the batch report.

## Interpretation rules

- Article-quality lint and raw-source searches are blocking findings: fix them before reporting completion.
- Missing ledger page references, case/batch-named durable pages, and shallow heavy-evidence pages are blocking findings.
- Evidence-audit warnings such as `page_claims_no_data_points` are advisory for cross-cutting role/process/governance/evaluation pages when their claims are synthesis over the corpus rather than direct source snippets. Report them honestly, but do not treat them as failure if there are no orphan links, missing records, or raw-source findings.
- Topic discovery returns candidates, not commands. Ignore generic verbs and filler terms; act only when the candidate is a recurring operational mechanism, exact error, command/config key, supportability boundary, or workflow split.
- Never create pages or sections named for the quality pass, batch, source folder, or individual records.

## Good completion report

Keep the final report concise and factual:

- what pages or directories changed;
- what reusable claims/data points were promoted;
- what noise was removed;
- DB counts after refresh;
- lint/audit verification results;
- remaining advisory warnings, if any.
