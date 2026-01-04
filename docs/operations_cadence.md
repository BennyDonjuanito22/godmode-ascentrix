# Operations Cadence & Planning

## Short-Term Focus (Weeks 1–6)

1. **Stabilize Autonomy**
   - Provision valid API/LLM keys and store them outside git.
   - Add pre/post-run smoke tests around `scripts/run_agent.sh` and `scripts/start_autopilot.sh`.
   - Wire HUD widgets to `/hud/*` endpoints so dashboards show realtime data.
2. **Execute Specialized Tasks**
   - Close fixer #12 (ledger health), researcher #13 (B3 traffic research), promoter #14 (B1 blitz) to validate profile-specific guardrails.
3. **Instrument Revenue**
   - Require every sale to run `scripts/record_revenue.py`.
   - Use `scripts/check_ledger_health.py` after ledger-related changes.
   - Surface rolling metrics (today/7d/30d + per-funnel) automatically in the HUD.
4. **Security Hygiene**
   - Rotate secrets, document incidents, and keep `design_docs/security_plan.md` up to date.

## Long-Term Vision

- Redundant infrastructure: multi-region nodes, automated backups/restore drills.
- Advanced security: encrypted channels, hardened firewalls, intrusion monitoring, Telegram-level resilience.
- Intelligence & telemetry: Qdrant vector memory + richer analytics so autopilot reprioritizes work based on ROI.
- Governance: legal/policy docs and SOC-style audit trail as revenue grows.

## Meeting Cadence

| Frequency | Agenda | Outputs |
| --- | --- | --- |
| Weekly (Security & Infra) | Secrets status, backup results, incident review, ledger health, open vulnerabilities | Action items + tasks in `api/tasks/roadmap.jsonl` |
| Bi-weekly (Product/Expansion) | HUD status, revenue funnels, agent KPIs, backlog grooming | Updated roadmap priorities, new tasks if needed |
| Monthly (Strategy) | Infra replication budget, security roadmap, new business lines, capital allocation | Updated long-term plan + infra/security upgrades |

Each meeting should:
- Capture notes (store in `memory/notes.jsonl` tagged with `meeting:<type>`).
- Update relevant docs/tasks.
- Revisit risks and confirm owners.

## Security/Infra Review Template (Weekly)

1. Check `scripts/check_ledger_health.py`.
2. Confirm secrets inventory (no plaintext in repo/logs).
3. Review backups (ledger, design docs, memory).
4. Document any incidents or anomalies.
5. Create fixer/security tasks as needed.

## Expansion Review Template (Bi-weekly)

1. HUD status (data freshness, API health).
2. Revenue funnel metrics + experiments.
3. Agent performance (success/failure rates per profile).
4. Roadmap adjustments.

## Strategy Session Template (Monthly)

1. Financial snapshot + runway.
2. Infra scaling milestones (multi-node, redundancy).
3. Security roadmap (next investments).
4. New business opportunities & research agenda.
5. Assign owners for the next month’s big rocks.
