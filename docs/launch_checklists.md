# Launch Execution Checklist

Use this list when we want the B1 Automation toolkit live and generating cash without babysitting.

## Immediate “Go Live” Steps
1. **Swap CTA URL** – Replace `config/funnels/b1.json` → `cta_url` (and every staged asset) with the real Stripe/Gumroad checkout. Commit the change and redeploy `api`.
2. **Smoke-test funnel** – `python3 -m http.client localhost:5051` or hit the landing page to confirm the CTA points to the production checkout and `/funnels/b1/lead` writes to `finance/leads.jsonl`.
3. **Publish promo wave #1** – Ship the TikTok/Shorts/LinkedIn/email pieces under `content/output/b1/*`, capture live URLs + metrics, and update `docs/b1_promo_log.md`.
4. **Trigger nurture + ledger logging** – `python3 scripts/nurture_leads.py send --limit 25`, then record actual conversions with `python3 scripts/nurture_leads.py convert --email <lead> --amount <price> --source <platform>`.
5. **Refresh dashboards** – `python3 scripts/lead_pipeline.py --output both` so HUD + partners see fresh stats; add a cron/Autopilot task to run nightly.
6. **Verify Autopilot loop** – `./scripts/start_autopilot.sh`, `docker compose -p godmode ps`, and tail `docker compose -p godmode logs autopilot` to ensure IDs 31–35 (daily practice) start resolving plus any revenue tasks you add.
7. **Backup + key rotation** – Run `scripts/ascentrix-backup.sh` (or manual tar) and confirm `~/.config/godmode/openai_key` holds the current secret.

## Ongoing Daily Tasks
1. Re-run `python3 scripts/schedule_skill_tasks.py --date $(date -I)` via cron so every agent gets fresh practice IDs.
2. Scan `reports/builder_practice_*.md`, `content/output/b1/practice_*.md`, `logs/autopilot_runs/*.log` to ensure practice outputs exist.
3. Review `docs/b1_promo_log.md` and queue the next 24h of assets (scripts already staged).
4. Respond to warm partners logged in `docs/b1_affiliate_outreach.md` and `finance/leads.jsonl`.
5. Feed notable learnings into `memory/notes.jsonl` for future agents.

---

# Full Build-Out Checklist

This list covers everything we still need for the “100% automated, multi-business” vision.

## Revenue Expansion
1. **Marketplace rollout** – Use `docs/b1_multiplatform_kit.md` + `docs/marketplaces_research.md` to launch B1 on Gumroad → Lemon Squeezy → Etsy, then march through the remaining 12 platforms (log each in `docs/b1_promo_log.md`).
2. **Checkout proof pack** – Add screen recordings/testimonials for each platform listing and store under `content/output/b1/proof/`.
3. **B2/B3/B4 funnels** – Clone the `businesses/b1` structure using `docs/funnel_framework.md`; assign roadmap tasks for each stream.
4. **Partner/affiliate automation** – Expand `scripts/nurture_leads.py` to auto-generate affiliate links + status updates; expose the metrics in HUD.

## Autonomy & Learning
1. Seed more builder/fixer katas under `playground/katas/` and wire `scripts/run_builder_practice.py` to pick random exercises.
2. Add guardian tasks per business: security sweep, upgrade hunt, self-study, and report export (PDF) saved alongside each business folder.
3. Schedule all practice + pipeline scripts via cron/Launchd on the Mac mini so they persist if the terminal session closes.
4. Capture weekly retros in `memory/notes.jsonl` tagged `["autonomy","retro"]` plus follow-up tasks.

## Infra & Security
1. Autostart Docker stack on boot (`launchd` job that runs `gmup` or `docker compose up -d`).
2. Harden containers (non-root user for API/autopilot, pinned dependency hashes, health-check alerts).
3. Automate backups (ledger, leads, notes, design_docs) to `backups/` + offsite sync.
4. Rotate API keys every week; document in `design_docs/security_plan.md`.
5. Expand monitoring – capture `docker compose ps` + HUD/API health snapshots into `logs/autopilot_runs/` every hour (Autopilot task).

## Product / HUD
1. Wire HUD widgets to live promo + ledger metrics (link `docs/b1_promo_log.md`, `reports/lead_pipeline.md`, ledger rollups).
2. Add “Practice Monitor” panel showing completion state of IDs 31–35 each day.
3. Implement marketplace tracker UI (source `docs/marketplaces_research.md`).

## Knowledge Replication
1. Export each business’s SOP bundle (Notion export, prompt packs, scripts) to a `knowledge_packs/<business>/` folder so new nodes can sync instantly.
2. Version the learning outputs (practice reports, research notes) and surface them in HUD > Agents for quick onboarding.

Work this list top-to-bottom whenever you ask “what’s next?” – it keeps us laser-focused on making the system earn autonomously while it learns every day.

