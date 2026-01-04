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
- The script POSTs to `http://127.0.0.1:5051/finance/ledger`. Update `API_URL` if calling a remote deployment.
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
