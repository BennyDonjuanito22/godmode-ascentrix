# God Mode Security Plan

## Goals

- Protect API keys, credentials, and financial data.
- Limit blast radius:
  - One compromised node should not destroy everything.
- Keep a clear audit trail of critical actions.

## Secrets Handling

- API keys (OpenAI, payment, etc.):
  - Stored in environment variables or secret files (not in git).
  - Referenced only by name in code.
- Config files:
  - Separate public config (display settings) from secrets.

## Network

- Use Tailscale for node-to-node communication.
- No direct public exposure of:
  - Postgres
  - Redis
  - Qdrant
- HUD/API exposure:
  - If exposed to the public internet, must be behind:
    - Authentication (API key, login).
    - HTTPS termination.

## Access Control

- Roles (planned):
  - Owner (full control).
  - Operator (see dashboards, restart agents/streams).
- Later:
  - Per-stream permissions and fine-grained API keys.

## Logging & Audit

- Log all:
  - Autopilot task transitions (pending→running→done/failed).
  - Agent task runs and their errors.
- Future:
  - Mark critical actions (e.g. deleting data, pausing all streams) and log them with extra detail.

## Web & Client Interfaces

- Existing HUD:
  - Must not expose sensitive secrets in UI.
  - Only shows high-level info and configuration references.

- Future desktop/mobile clients:
  - Treat them as **untrusted frontends** that talk to secured APIs.
  - Never embed API keys or secrets directly.

## Agent Rules

- Agents must:
  - Never write secrets to logs.
  - Never commit secrets to git.
  - Treat external API errors as temporary unless clearly fatal.
- Agents may:
  - Propose security hardening tasks but should not break operator access.

## Incident Response (Future)

- Define playbooks for:
  - Key leakage.
  - Node compromise.
- At minimum:
  - Rotate keys.
  - Rebuild compromised node.
  - Inspect logs for hostile actions.

## Resilience & Redundancy (Future-Funded)

- Target architecture:
  - Multiple nodes in different regions/providers (mirrored repos, design docs, ledger, vector memory).
  - Health checks + failover scripts so the stack survives hardware loss or attacks.
- Backups:
  - Nightly snapshots of `finance/ledger.jsonl`, `design_docs/`, `memory/`.
  - Test restores monthly (tie into the strategy session agenda).
- Network hardening:
  - Restrict SSH/remote access via Tailscale ACLs.
  - Enforce TLS everywhere; long term aim for end-to-end encrypted channels similar to Telegram’s security posture.

## Monitoring & Cadence

- Weekly security/infra meeting (see `docs/operations_cadence.md`).
- Use `scripts/check_ledger_health.py` after ledger-affecting changes.
- Store meeting notes in `memory/notes.jsonl` with tags `security` and `infra`.
- Any anomaly should produce a new task in `api/tasks/roadmap.jsonl` with `agent_type` = `fixer` or `researcher`.

## AUTOGEN: Agent Security Rules

Agents must follow these rules when modifying the system:

- Never write API keys or secrets into:
  - Design docs.
  - Logs.
  - Git commits.
- When adding new external integrations:
  - Store credentials only in env/secret storage.
  - Document required env vars, not the values.
- For any major change to authentication or access:
  - Create/update a task describing the change.
  - Update security_plan.md with rationale and details.

If an agent detects suspicious behavior (e.g. repeated auth failures, unexpected
traffic patterns), it should:
- Log the event.
- Create or update a security-related task in tasks/roadmap.jsonl for human review.
