# Salesforce Case Folder Ingest Notes

Use this reference when ingesting exported Salesforce support-case folders where each case is a directory containing `case.json`, `index.json`, `linked/*.json`, and `related/*.json`.

## Source discovery

- Count actual case directories by the presence of `case.json`; do not trust archive/folder names like `next_2000` as the source count.
- Ignore Mac archive noise (`.DS_Store`, `__MACOSX`, `._*`) and any directory without `case.json`.
- Record a batch-report note when the directory name implies more cases than are present on disk.

## Per-case review shape

For each case, read at least:

1. `case.json` — central classification and work signals: `CaseNumber`, `Id`, `Subject`, `Purpose_of_Engagement__c`, `Problem__c`, `Cause__c`, `Solution__c`, `Priority`, `Region__c`, `Deployment_Location__c`, `Environment_Of_Issue__c`, `Origin`, `Status`, owner/queue fields, satisfaction/reopen/escalation flags.
2. `related/case_history.json` — status and owner transitions; often the best lifecycle/process evidence.
3. `related/email_messages.json` — customer-facing asks, assignment language, scheduling, clarifications; absent in many cases, so treat absence as unknown rather than no communication.
4. `related/tasks.json`, `events.json`, `case_feed.json` — activity and lifecycle context when present.
5. `related/content_versions.json` / content document files — supporting artifact metadata. Do not copy binary content into the wiki; cite the case and keep source_ref in the ledger.
6. `linked/*.json` — account/contact/owner context only when it changes classification, routing, evidence, or governance. Avoid surfacing customer-identifying detail into durable pages.

## Distillation rules specific to Salesforce exports

- Use the human-facing `CaseNumber` in citations and ledger `case_id`; use `salesforce:<Id> <folder path>` in `source_ref`.
- Sanitize ledger `gist` and `notes`: strip email addresses, phone numbers, credentials, and customer-identifying strings where possible.
- Treat template/legal/signature/pricing fields as object-model noise unless a case proves operational relevance; document them once as ignored fields rather than counting them as evidence repeatedly.
- Separate lifecycle closure from resolution substance: `Status=Completed` is not proof of a well-evidenced root cause or reusable solution.
- Sparse `Problem__c`, `Cause__c`, or `Solution__c` should produce explicit `unknown:<reason>` classifications instead of guessed root cause.

## Bootstrap page-budget guard

Salesforce exports can contain many recurring topics. During a new-wiki bootstrap:

- Keep topic distributions in aggregate pages such as `concepts/product-and-environment-signals.md` and `concepts/engagement-types.md` until the taxonomy stabilizes.
- Do not create one topic page per high-frequency purpose during the first pass unless the concept truly cannot fit an existing aggregate page.
- Keep stage specifics in `process/overview.md` unless evidence justifies splitting stage pages; this helps stay within the ~25-page bootstrap budget.

## Verification checklist

After writing the wiki, mechanically verify:

- Durable page count is within bootstrap budget.
- `_meta/ingest-ledger.csv` has one row per discovered `case.json` folder.
- No durable page name contains a case number, Salesforce record ID, batch/run name, or source folder token.
- Every `pages_updated` ledger reference points to an existing page.
- Gists/notes do not contain raw email addresses or phone numbers.
- `_meta/batches/<batch-id>/report.md` exists and states source count, processed count, novelty rate, taxonomy changes, bloat-detector result, and open questions.
