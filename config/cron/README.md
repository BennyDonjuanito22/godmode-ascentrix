# Cron / Launchd Configuration

1. Adjust `config/cron/godmode.cron` so `GODMODE` points to your repo path.  
2. Install the entries with `crontab config/cron/godmode.cron`.  
3. Logs are written to `logs/cron/*.log`.

Jobs included:
- `cron_schedule_skill_tasks.sh` – appends Autopilot practice tasks every midnight.
- `cron_lead_pipeline.sh` – regenerates Markdown + CSV lead dashboards daily.
- `cron_nurture_followups.sh` – runs the nurture CLI hourly (override `NURTURE_LIMIT` if needed).
