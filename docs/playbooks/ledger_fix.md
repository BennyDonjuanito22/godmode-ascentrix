# Ledger Fix Playbook

Use this guide whenever ledger functionality regresses or the JSONL file looks suspicious.

1. **Run the health script**
   ```bash
   ./scripts/check_ledger_health.py
   ```
   - If the ledger is missing, confirm `finance/` is mounted and permissions allow writes.
   - If parsing fails, note the reported line and inspect it manually.

2. **Repair corrupted lines**
   - Open `finance/ledger.jsonl` in a text editor.
   - Delete malformed lines or fix JSON syntax.
   - Re-run the health script to confirm the file parses.

3. **Verify API/CLI**
   - Hit `GET /finance/ledger` and `GET /finance/summary` (using curl or browser) to confirm endpoints still respond.
   - Record a test entry:
     ```bash
     python scripts/record_revenue.py --amount 0.01 --currency USD --source test --funnel B1 --notes "ledger check"
     ./scripts/check_ledger_health.py
     ```
   - Remove the test entry afterward if desired.

4. **Document the fix**
   - Log findings in `memory/notes.jsonl` with tags `ledger` and `fixer`.
   - Update this playbook if new failure modes appear.

5. **Create follow-up tasks**
   - If the regression requires code changes, open a `fixer` task in `api/tasks/roadmap.jsonl`.
   - Attach details (links to commits, log excerpts) so future agents can trace the issue.
