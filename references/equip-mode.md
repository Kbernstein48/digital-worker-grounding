# Equip Mode — From Trained Wiki to Built Tooling

Authoritative reference for the **Equip** operating mode in `SKILL.md`. Equip closes
the gap between *knowing the work* (Ingest/Deepen) and *doing the work* (built,
deployed tools on the UiPath platform). Load this file whenever generating a tool
manifest, writing build briefs, or handing builds to builder skills.

## The idea

After ingestion, the wiki knows what the work **is**: every resolution pattern, every
system touched, every actor, every recurring diagnostic step — all evidence-linked in
`_meta/knowledge.db`. Equip mode mines that same database to determine what the worker
**needs**: a ranked, evidence-backed manifest of tools that would let the worker execute
(not just describe) the resolution patterns it has learned. It then prepares a
self-contained build brief per tool and hands each one to the appropriate UiPath builder
skill (`uipath-rpa`, `uipath-agents`, `uipath-maestro-flow`, `uipath-connector-builder`,
`uipath-human-in-the-loop`, orchestrated via `uipath-planner`) to construct it on the
platform.

The worker literally equips itself — under the governance the Role OS already defines.

## Pipeline

```
Ingest/Deepen ──▶ 1. Gap analysis ──▶ 2. Tool manifest ──▶ 3. Approval gate
                     (mine the DB)       (ranked, cited)      (Self-Extension Policy)
                                                                    │
        5. Register & take over ◀── 4. Builder handoffs ◀───────────┘
           (tools/ pages, Role OS      (PDD/SDD → uipath-planner
            authority, coverage %)      → specialist skills)
```

### 1. Capability-gap analysis

Mine `knowledge.db` — no new data collection needed:

| Source | What it yields |
|---|---|
| `cases.resolution_pattern` | The verbs of the job. Cluster them; each cluster is a candidate capability. |
| `cases.systems` | Systems the worker must touch → connector/integration needs. |
| `cases.actors` | Who acts today → which steps are candidates for takeover vs. HITL. |
| `signatures` | Error signatures → diagnostic tools (log parsers, connectivity probes). |
| `data_points` | Values repeatedly extracted by hand → extraction/lookup tools. |
| `claims` (procedure kind) | Multi-step procedures → automatable workflows. |

Classify every resolution-pattern cluster into three buckets:

- **Knowledge-only** — the trained agent can already handle it (answer, diagnose, draft).
- **Tool-required** — needs an action the agent cannot perform: call an API, run a
  script on a machine, update a record, collect artifacts.
- **Human-only** — outside the Role OS authority boundaries; becomes an escalation or
  approval surface, not a tool.

### 2. The tool manifest

Written to `_meta/tool-manifest.yaml`. Every entry is evidence-backed — the same
provenance discipline as wiki claims. Ranking = case frequency × feasibility.

```yaml
- tool_id: orchestrator-connectivity-probe
  purpose: Test outbound connectivity from a robot machine to Orchestrator
    (ports, proxy, TLS chain) and return a structured verdict.
  tool_type: coded-workflow          # → uipath-rpa (.cs) or uipath-functions
  execution_locus: in-network        # see "Execution locus" below
  evidence:
    case_count: 25
    exemplars: [02896887, 02818325, 02841666]
    concept_pages: [concepts/network-proxy-firewall-dns.md]
  contract:
    inputs:  { machine: string, orchestrator_url: string }
    outputs: { reachable: bool, failing_layer: enum, detail: string }
  authority: autonomous              # per role-os authority matrix
  acceptance_fixtures: 3             # replayed from source cases
- tool_id: salesforce-case-updater
  purpose: Post the drafted customer communication and status update back to the case.
  tool_type: is-connector-call       # → uipath-platform (Salesforce connection exists)
  execution_locus: platform-api
  authority: approval-gated          # outward-facing → HITL
  ...
```

#### Execution locus (mandatory per entry)

Derive from the deployment mix of the entry's citing cases — never assume the tool's
target is reachable from where the tool runs. A probe pointed at a private FQDN from
outside the network reports the very failure it is meant to diagnose.

| Locus | When | Shape of the tool |
|---|---|---|
| `in-network` | The worker's robots run inside the network that owns the target (internal digital worker over the org's own systems) | Unattended workflow/job; direct checks are valid |
| `remote-assisted` | The worker has no foothold in the target environment (e.g. a support worker diagnosing customer systems) | Two halves: a **generator** that emits a parameterized, read-only diagnostic script for the environment owner to run, plus a **parser** that ingests the returned output and runs signature matching |
| `platform-api` | The target is a SaaS/platform API reachable with an existing connection | IS connector call or API workflow |
| `public` | The target is genuinely public (public DNS, cloud endpoints) — verify this from the case deployment fields | Direct probe, but it must refuse or downgrade to `remote-assisted` when the target does not resolve publicly |

If the citing cases mix deployment contexts (e.g. 65% on-premises, 35% cloud), the
manifest entry either splits into locus-specific variants or specifies the
`remote-assisted` shape as the common denominator.

### 3. Approval gate

The manifest is a **proposal**, never self-executing. This is exactly the hook the Role
OS **Self-Extension Policy** section defines: how the worker proposes, tests, and
governs changes to its own tools. Ship the manifest as a HITL approval (via
`uipath-human-in-the-loop` action app, or simply a reviewed PR) before any build starts.
Humans can strike, re-rank, or re-scope entries.

### 4. Builder handoffs — the skill conversation

For each approved entry, Equip emits a **self-contained build brief**: goal, IO
contract, authority tier, the evidence cases that motivated it, and acceptance fixtures
derived from those cases (given case X's real inputs, the tool must produce the outcome
the human eventually reached). The brief must stand alone — the builder skill gets no
other context.

Routing table:

| `tool_type` | Builder skill |
|---|---|
| `rpa-workflow`, `coded-workflow` | `uipath-rpa` (.xaml / .cs) |
| `coded-function` (deterministic, no LLM) | `uipath-functions` |
| `agent-tool`, `sub-agent` | `uipath-agents` |
| `is-connector-call`, missing connector | `uipath-platform` / `uipath-connector-builder` |
| `orchestration`, `hitl-gate` | `uipath-maestro-flow` / `uipath-human-in-the-loop` |
| platform prerequisites (assets, queues, buckets, connections) | `uipath-platform` |

For a multi-tool manifest, don't drive specialists one-by-one: Equip authors a **PDD**
(process design document) describing the takeover, and hands it to `uipath-planner` —
which is purpose-built to turn a PDD into an SDD and derive the multi-skill,
multi-project task list. Equip's job ends at "well-formed PDD + per-tool briefs";
planning and sequencing belong to the planner.

Conversation mechanics (Claude Code): same-session `Skill` invocations for small
manifests; spawned per-tool build sessions (each seeded with one brief) for large ones;
a task backlog (`TaskCreate`) mirroring the manifest so progress is visible either way.

### 5. Registration and progressive takeover

A built tool is not done until the wiki knows about it:

- **`automation/tools/<tool-id>.md`** wiki page: what it does, contract, when to use it,
  evidence links to the cases it serves. Query mode can then answer "how do I fix X"
  with "run tool Y" instead of prose. (Lives under `automation/` — these pages are the
  built counterpart of that section's compile-down candidates.)
- **Role OS authority matrix** updated: which tools run autonomously vs. approval-gated.
- **Eval before trust**: the acceptance fixtures become the tool's eval set (runnable
  via `uipath-agents` / Maestro eval tooling). A tool enters *shadow mode* (proposes,
  human executes) before *autonomous mode*.
- **Coverage metric**: % of historical cases whose resolution pattern is now executable
  end-to-end with registered tools. This is the takeover progress bar — and a natural
  dashboard for `uipath-coded-apps` to render.

## Worked example (from the sample corpus)

From wiki-scaffold-v2's 885 UiPath support cases, gap analysis would surface roughly:

1. `orchestrator-connectivity-probe` — 25+ firewall/proxy/DNS cases (autonomous)
2. `cert-chain-inspector` — certificate/TLS trust cases (autonomous)
3. `robot-log-collector` — parse UiRobot logs / support bundles for known signatures (autonomous)
4. `salesforce-case-updater` — post comms + status via the existing Salesforce connection (approval-gated)
5. `escalation-action-app` — structured handoff when authority boundaries are hit (human-only surface)

Items 1–3 are diagnostics the agent currently *describes* in
`recommendednextaction`; once built, the same cases resolve without a human
executing steps by hand.

## Design tenets

- **Evidence in, evidence out.** A tool with no citing cases doesn't get proposed. Same
  hard-rule discipline as the wiki: signal over volume.
- **Guard signature quality.** Before matching or citing signatures, drop entries under
  a minimum specificity threshold (e.g. bare "error"/"errors" normalizations). If the
  signatures table is noisy, flag it as an upstream lint finding rather than building
  matchers on top of noise.
- **Never assume reachability.** Every entry carries an `execution_locus` derived from
  its citing cases' deployment contexts (see above).
- **Propose, never self-execute.** The manifest is governed by the Self-Extension
  Policy; the approval gate is not optional.
- **Briefs stand alone.** A builder skill (or a fresh session running it) must be able
  to build and test the tool from the brief alone.
- **Acceptance from history.** Real cases are the test fixtures — the corpus that
  trained the worker also certifies its tools.
- **The wiki stays the source of truth.** Tools are registered as wiki pages with
  provenance; the knowledge DB gains a `tools` table mirroring the manifest.
