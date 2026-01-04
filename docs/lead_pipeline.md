# Lead & Partner Pipeline Usage

We now maintain a structured report of `finance/leads.jsonl` grouped by lead type (landing, affiliate, partner). The automation lives at `scripts/lead_pipeline.py`.

## Running the script

```bash
python3 scripts/lead_pipeline.py --output both
```

Outputs:
- `reports/lead_pipeline.md` – Markdown summary (per lead type) for quick review in HUD/docs.
- `reports/lead_pipeline.csv` – Flat data for spreadsheets or BI tools.

## Lead type heuristics
- `metadata.tag` starting with `partner` → **partner** lead.
- `source` containing `affiliate` → **affiliate** lead.
- Everything else → **landing** lead (direct opt-ins or form captures).

## Workflow
1. Capture leads via `/funnels/b1/lead` (landing), or using affiliate/partner lead tags.
2. Run the script daily (Autopilot task 25) to refresh the dashboard.
3. Review `reports/lead_pipeline.md` for follow-up needs.
4. When a lead converts, use `python3 scripts/nurture_leads.py convert ...` to log revenue and update status.
5. Store notable insights in `memory/notes.jsonl` (tags `stream:B1`, `lead`).

The script is safe to call from Autopilot via `run_shell`. Add new heuristics as additional funnels/streams come online.
