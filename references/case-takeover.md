# Case Takeover Workflow

Use this reference when the Digital Worker is asked to take over a live or exported business record: support case, ticket, claim, order, incident, application, CRM object, document bundle, or any analogous source object.

The goal is an action packet, not a case summary. Source records remain the system of record; wiki pages hold reusable knowledge; `_meta/knowledge.db` is the queryable evidence index.

## Workflow

```text
receive record
  -> inspect source of truth
  -> query knowledge.db
  -> classify issue/object state
  -> gather missing evidence
  -> decide next action
  -> draft communication / escalation
  -> update reusable wiki knowledge
  -> refresh DB and verify
```

## 1. Receive and normalize

- Identify the source record ID and source-of-truth location.
- Build a sanitized intake snapshot: object type, status, owner, requested outcome, product/component/system, environment, version/topology, exact error or decision request, and available related artifacts.
- Redact secrets, tokens, connection strings, credentials, personal identifiers, and customer-specific names before durable storage.
- Mark whether the record is rich, sparse, closure-only, malformed, or missing artifacts.

## 2. Inspect source records first

If a live source or local source folder is available, inspect it before answering from the wiki.

Read:

- primary record fields;
- comments, email/messages, tasks/events/feed;
- attachments and logs;
- lifecycle/history/status transitions;
- related records and linked documents where available.

Keep source facts separate from interpretation. A closed/completed status proves lifecycle state, not root cause.

## 3. Query the knowledge DB

Use the generic DB tools to identify similar records, pages, claims, signatures, data points, and gaps:

```bash
python scripts/query_knowledge_db.py --wiki "$WIKI" search "<error-or-keyword>" --limit 20
python scripts/query_knowledge_db.py --wiki "$WIKI" data-points --term "<error-or-config-key>" --limit 20
python scripts/query_knowledge_db.py --wiki "$WIKI" claims --page "<candidate-page>" --limit 20
python scripts/record_inspector.py --wiki "$WIKI" <record-id>
python scripts/page_review.py --wiki "$WIKI" <candidate-page>
```

Do not paste query result text directly into pages. Convert it into sanitized reusable claims and cite source record IDs.

## 4. Classify the issue or object state

Classify by concrete signal, not only broad source-system labels:

- symptom/error/signature;
- product, system, or business process area;
- process stage;
- root-cause hypothesis;
- ownership boundary;
- supportability / policy / documentation boundary;
- risk level;
- evidence sufficiency.

For support cases, prefer operational layers such as prerequisite, SQL, TLS/certificates, DNS/proxy, registry/image, identity/SSO, RBAC, version path, DR/backup, infrastructure ownership, supportability boundary, or low-signal closure.

## 5. Gather missing evidence

Ask for the smallest evidence set that distinguishes the next branch:

- exact error text, command, timestamp, component, and affected scope;
- logs or command outputs;
- version, topology, deployment model, environment;
- owner of infrastructure or source-system control;
- screenshots only when the visual state matters;
- maintenance window, backup, rollback, and validation owner for production-impacting work;
- docs or policy references for supportability decisions.

If evidence is missing, say what is missing and why it matters.

## 6. Decide next action

Choose one:

1. **Answer now** — sufficient evidence, low risk, known page/pattern, clear validation.
2. **Request evidence** — branch cannot be distinguished yet.
3. **Route/escalate** — different owner, production risk, policy/supportability boundary, or product confirmation needed.
4. **Advisory boundary** — unsupported or not recommended path; provide safer alternative.
5. **Learning update only** — record is completed/low-signal and only updates durable knowledge.

Every next action must include validation criteria.

## 7. Draft communication

Use this structure:

```markdown
Current understanding:
Evidence reviewed:
Relevant wiki/DB matches:
Missing evidence / ask:
Recommended next action:
Validation criteria:
Risk / escalation boundary:
Learning-loop update:
```

Group by operational layer rather than message chronology.

## 8. Escalate deliberately

Escalate when:

- product defect, supportability exception, policy exception, or architecture approval is being asserted;
- production-impacting action lacks maintenance/rollback/validation controls;
- customer-owned infrastructure or another business owner must act;
- evidence is contradictory, missing, or too sparse;
- source data reveals possible secret/PII leakage that needs remediation.

Transfer the issue class, exact signal, evidence reviewed, missing evidence, relevant pages, and reason for escalation.

## 9. Update durable knowledge

After action or resolution:

- Update topic/process/playbook pages only with reusable claims.
- Do not create per-record pages or batch sections.
- Use citations and evidence counts.
- Refresh `_meta/knowledge.db` after substantial edits.
- Run article-quality lint and evidence audit before reporting completion.

## Done Criteria

A takeover is complete when the worker can state:

- what source records/artifacts were inspected;
- what issue/object state was assigned;
- which wiki pages and DB rows support the classification;
- what evidence is sufficient or missing;
- what next action and validation criteria apply;
- what communication or escalation is needed;
- whether reusable wiki knowledge changed;
- what verification was run.
