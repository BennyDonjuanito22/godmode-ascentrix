# Finance Ledger – Minimal Logging Workflow

The repository now ships with a JSONL ledger plus API helpers so God Mode can track revenue per day and per funnel before a full Postgres pipeline exists.

## Storage

- File: `finance/ledger.jsonl`
- Format: one JSON object per line with fields:
  - `timestamp` (Unix seconds, float)
  - `amount` (positive = revenue, negative = expenses/refunds)
  - `currency` (ISO code)
  - `source` (e.g., stripe, shopify, affiliate_platform)
  - `funnel` (B1, B2, B3, B4, etc.)
  - `notes` (freeform memo)

## API Endpoints (FastAPI in `api/app.py`)

- `GET /finance/ledger?limit=50` – returns recent entries.
- `POST /finance/ledger` – append a new entry. Required JSON fields: `amount`, `currency`, `source`, `funnel`, `notes`.
- `GET /finance/summary` – aggregates per-day totals and per-funnel totals for HUD widgets.

Under the hood, `api/ledger.py` contains helper functions for appending, reading, and summarizing entries.

## CLI Helper

- Script: `scripts/record_revenue.py`
- Usage:
  ```bash
  ./scripts/record_revenue.py \
    --amount 149.00 \
    --currency USD \
    --source stripe \
    --funnel B1 \
    --notes "Customer bought AI Toolkit"
```
- The script POSTs to `http://127.0.0.1:${GODMODE_API_PORT_HOST:-5051}/finance/ledger`. Update `GODMODE_API_URL` if calling a remote deployment.
- Autopilot / agents can invoke it via `run_shell`:
  ```json
  {
    "tool": "run_shell",
    "tool_input": {"cmd": "python scripts/record_revenue.py --amount 149 --currency USD --source stripe --funnel B1 --notes \"AI Toolkit sale\""}
  }
  ```
  This keeps ledger writes consistent without embedding API logic in every agent.
- Health check: run `./scripts/check_ledger_health.py` after ledger-affecting changes to ensure the JSONL file still parses and totals look correct. See `docs/playbooks/ledger_fix.md` if the script reports issues.

## HUD Integration Roadmap

- Home screen: revenue widgets should read `/finance/summary` for Today / 7-day / 30-day metrics.
- Streams detail: show per-funnel totals for B1–B4.
- Logs / Memory: optionally list the last ledger entries for auditing.

## Future Enhancements

- Move data to Postgres once migration tooling is in place (keep JSONL as backup).
- Add authentication/authorization if exposing endpoints publicly.
- Automate ingestion from Stripe/Shopify exports via a cron-style agent task.
- Emit ledger writes as notes (e.g., `stream:B1` tags) for cross-linking with memory.

## Mock Data and Missing Payment Keys Behavior

When Stripe, Gumroad, or Digistore API keys are missing from the configuration, the system falls back to mock mode for financial data:

- Revenue and sales metrics will show zero balances.
- A `mock_data` flag will be set to `true` in HUD/status API responses to indicate data is simulated.
- This prevents misleading financial reporting when live keys are not configured.

Ensure your environment variables or config files include valid keys for these platforms to see real-time financial data.

## CTA URLs and Instant Payout Links

The CTA URLs in funnel configurations (e.g., `config/funnels/b1.json`) must be aligned with the instant payout links used in promotions and payouts.

- For example, the B1 funnel uses `https://pay.godmodehq.com/instant/b1` as the CTA URL.
- This URL should match the instant payout link pattern to ensure consistency across the system.

Verify and update funnel config files to keep these URLs synchronized.

## Payout Processing Operational Guardrails

To ensure consistent and auditable payout processing, the system provides a canonical payout API and service:

- **API Endpoints:**
  - `POST /api/payouts/create` - Create a new payout record with business ID, net amount, status (default 'pending'), and optional note.
  - `POST /api/payouts/update_status` - Update the status of an existing payout by payout ID.
  - `GET /api/payouts/list` - List payouts for a business, optionally filtered by status.
  - `GET /api/payouts/{payout_id}` - Retrieve details of a single payout by ID.

- **Service Functions:**
  - `create_payout(business_id, net_amount, status='pending', note=None)`
  - `update_payout_status(payout_id, new_status)`
  - `list_payouts(business_id, status_filter=None)`
  - `get_payout(payout_id)`

- **Database:**
  - The `payouts` table stores payout records with fields for business ID, net amount, status, note, created_at, and updated_at timestamps.

- **Usage:**
  - Use these APIs to create payout records when initiating payouts.
  - Update payout status to 'paid' or other statuses as payouts are processed.
  - Query payouts for reporting and reconciliation.

- **Error Handling:**
  - API endpoints return HTTP 400 for invalid input or processing errors.
  - 404 is returned if a requested payout is not found.

- **Integration:**
  - The metrics API aggregates payout totals from the `payouts` table for display in the HUD.

These guardrails ensure payout processing is auditable, consistent, and integrated with financial reporting.

## Recent Enhancements to HUD Data Handling

- The `_business_snapshots` function in `api/hud_api.py` now explicitly sets zero balances for revenue and recent buyers when keys are missing to prevent misleading financial data.
- It marks a `mock_data` flag as `true` in HUD/status API responses when no real revenue or email accounts exist, indicating simulated data.
- CTA URLs are checked for the presence of `pay.godmode` to align with instant payout links, setting an `instant_payout` boolean flag.
- These changes improve accuracy and clarity of financial reporting in the HUD and ensure CTA consistency with payout workflows.


## Zero Balances and Mock Data Flag in HUD/Status

- The `_business_snapshots` function in `api/hud_api.py` ensures that when payment API keys are missing or no email accounts exist, revenue and recent buyer counts are zeroed to prevent misleading financial data.
- A `mock_data` boolean flag is set to `true` in the HUD/status API responses to clearly indicate that the financial data is simulated.
- This behavior helps operators distinguish between real and mock financial data in the HUD.

## CTA Alignment with Instant-Pay Links

- The CTA URLs in funnel configurations and HUD snapshots are checked for the presence of `pay.godmode` to identify instant payout links.
- An `instant_payout` boolean flag is set accordingly in the HUD data to reflect this alignment.
- This ensures consistency between promotional CTAs and payout workflows, improving user experience and tracking.
