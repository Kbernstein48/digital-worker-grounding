# Source-Case Deepening: Turning Reference Cases into Operational Meat

Use this reference when a grounding wiki technically has ledger coverage and pages, but the pages still read like high-level summaries, taxonomy distributions, or lists of reference cases rather than actionable knowledge.

## Trigger signals

Run a deepening pass when:

- the user says the wiki focuses too much on reference cases or high-level summaries;
- pages mostly say what categories occurred instead of what was discussed, observed, fixed, decided, or ruled out;
- pages cite many cases but do not contain exact symptoms, commands, config keys, decision criteria, environment preconditions, pitfalls, or support communication moves;
- generated sections contain customer/case-flavored observations such as `<customer> - Automation Suite Install/Upgrade - EMEA` instead of reusable operational knowledge.

## Principle

A case citation is not the content. The source case is the evidence well. The page should contain the extracted meat:

- exact blocker/error/signature;
- cause or likely boundary;
- environment/version/deployment preconditions;
- command/config key/path/UI step;
- decision criterion or supportability boundary;
- workaround and why it is exceptional;
- validation check;
- reusable communication move.

The ledger keeps the case pointer and gist. Durable pages should not retell cases or list case references as the main artifact.

## Deepening workflow

1. Orient as usual: read `SCHEMA.md`, `index.md`, `log.md`, and `_meta/topic-map.md` if present.
2. For each page, use `_meta/ingest-ledger.csv` `pages_updated` to find source cases mapped to that page.
3. Reopen those source cases and read the case record plus relevant related artifacts:
   - `case.json` fields: `Problem__c`, `Cause__c`, `Solution__c`, `Purpose_of_Engagement__c`, deployment/environment fields, version fields.
   - related history/feed/tasks/events/emails when present, but do not copy thread prose.
   - attachment/content metadata as evidence that support material exists; do not copy binaries into pages unless the wiki is explicitly using a `raw/` escape hatch.
4. Extract reusable units only when they pass the worker test: a future handler could use the unit to route, diagnose, act, verify, communicate, or escalate.
5. Merge the unit into the appropriate existing section or create a more specific topic page when the unit is a recurring/substantial pattern hidden inside an umbrella page.
6. Remove or replace generated summary sections that are not actionable, especially:
   - distribution summaries in durable pages (keep distributions in `_meta/` reports);
   - “Observed operational signal: <customer/topic/region>” bullets;
   - “this page distills N cases” as the only detail;
   - case-reference lists outside the ledger/evaluations golden-case exception.
7. Update `index.md`, `_meta/topic-map.md`, `log.md`, and the batch report with the deepening pass and verification results.

## Good page shape after deepening

Prefer blocks like:

```markdown
### JDBC / SQL Server TLS trust-chain failure during prereq
**Symptom**: Automation Suite prerequisite SQL checks can fail at `SQL (PRODUCT-AICENTER, TYPE-JDBC)` with the driver reporting `trustServerCertificate=false` and an inability to build a valid certification path to SQL Server. (evidence: 1 case — e.g. 02659290)
**What to inspect**:
1. Confirm which product check failed; a single product-specific JDBC check can fail while the rest of prereq output looks healthy.
2. Preserve exact TLS phrases such as `trustServerCertificate`, `PKIX`, and `unable to find valid certification path`; they route the issue to SQL certificate trust, not generic database reachability.
3. Verify whether the SQL Server certificate chain is trusted by the node/runtime performing the check before changing product configuration.
**Pitfall**: bypassing installer logic is an exceptional workaround that requires specialist validation, not a default fix path. (evidence: 1 case — e.g. 02659290)
```

Avoid blocks like:

```markdown
- This topic appeared in 54 cases.
- Observed operational signal: <customer> - Automation Suite Install/Upgrade - EMEA.
- Case 02659290 was about a customer upgrade and SQL errors.
```

## Source-text filters

When extracting from Salesforce exports, aggressively filter out noise before writing durable pages:

- email headers: `From:`, `To:`, `CC:`, `BCC:`, `Sent:`, `Subject:`;
- signatures, greetings, disclaimers, confidentiality notices;
- scheduling-only chatter (`send the invite`, `available tomorrow`, `please reply with time`), unless the destination is a communication playbook and the reusable move is generalized;
- customer names, person names, account names, email addresses, phone numbers, hostnames, internal mentions, thread IDs, image CIDs;
- legal/template/pricing boilerplate;
- closure-only text (`Completed`, `Done`, `N/A`, `task completed`) unless the page is explicitly about low-signal closure handling.

Sanitize with placeholders such as `<customer-or-person>`, `<host>`, `<email>`, and `<phone>` when exact identity is not the reusable signal.

## Split-out page criteria during deepening

Create a new topic page when a specific operational pattern is hidden inside a broad page and has at least one of:

- recurring evidence;
- a rare-but-important supportability boundary;
- a reusable exact signature or command/config sequence;
- a decision that changes routing or risk.

Examples of valid split-outs from Automation Suite / support exports:

- `temp-registry-and-airgap-image-seeding.md`
- `core-dns-custom-resolver.md`
- `sql-tls-and-trustservercertificate.md`
- `classic-folder-job-state-blockers.md`
- `vdi-server-side-orchestrator-risk.md`

These are topic pages because a future worker would search for the specific symptom/boundary, not the original case.

## Verification after deepening

Mechanically check:

- ledger row count still equals discovered cases;
- every `pages_updated` reference exists;
- no durable page name contains case IDs, Salesforce IDs, source-folder tokens, or batch/run names;
- no durable pages contain raw email addresses, phone numbers, email headers, confidentiality disclaimers, thread IDs, or customer/person names spotted in snippets;
- pages citing ≥20 cases are not thin and contain operational detail;
- new split-out pages are in `index.md` and `_meta/topic-map.md`;
- `log.md` and batch report record what was deepened and what lint found.
