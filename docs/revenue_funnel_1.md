# B1 Funnel (AI Growth Toolkit) – Configuration Guide

This document explains how to customize and deploy the placeholder landing page/endpoint that now ships with the repository.

## Components

- **API endpoint**: `GET /funnels/b1` returns the JSON configuration currently in use.
- **Landing page**: `GET /funnels/b1/landing` renders a single-page experience with headline, bullets, CTA button, testimonial badge, and fine print.
- **Config file**: `config/funnels/b1.json` stores the copy/CTA used by both endpoints. When no file exists, defaults are generated automatically.

## Customization Steps

1. Edit `config/funnels/b1.json`:
   - `hero_title` / `hero_subtitle`: headline and supporting copy.
   - `bullets`: list of key benefits (array of strings).
   - `cta_label`: text on the button.
   - `cta_url`: **replace this with the real Stripe/Gumroad checkout link** (the landing page button and nurture emails both use it).
   - `proof`, `testimonial_label`, `fine_print`: trust elements and disclaimers.
2. Save the file and restart the API service (or trigger a reload) so FastAPI reads the new values.
3. Hit `http://127.0.0.1:${GODMODE_API_PORT_HOST:-5051}/funnels/b1/landing` in a browser to verify the page renders with the updated copy.

## Checkout + Lead Capture

- The landing page now includes an email capture form wired to `POST /funnels/b1/lead`.
- Submissions land in `finance/leads.jsonl` with `status="new"` and metadata containing the source tag (drawn from `?utm_source=` query params when available).
- Successful submissions show inline confirmation; failures surface an error so you can debug the API locally.
- The lead API is intentionally simple so autopilot or operators can inspect entries via `GET /funnels/b1/lead?limit=100`.

### Verifying the flow

1. Open `http://127.0.0.1:${GODMODE_API_PORT_HOST:-5051}/funnels/b1/landing`.
2. Submit an email; confirm the toast appears.
3. Check `finance/leads.jsonl` (or `GET /funnels/b1/lead`) to ensure the entry exists.
4. Once a lead pays, run `python scripts/nurture_leads.py convert --email bob@example.com --amount 97 --source gumroad --notes "Launch day sale"` to log the conversion and auto-call the ledger CLI.

## Nurture Workflow

- `scripts/nurture_leads.py send --limit 10` pulls the newest leads, generates a follow-up email referencing the CTA link, logs the copy to `logs/nurture_runs/`, and marks each lead as `contacted`.
- `scripts/nurture_leads.py convert --email alice@example.com --amount 97 --source gumroad` runs `scripts/record_revenue.py` for you and updates the lead to `converted`.
- These commands are safe for Autopilot (`run_shell ["python3", "scripts/nurture_leads.py", ...]`) and give you an auditable trail in git.

## HUD Integration

- The Streams detail card lists the landing page URL so operators can click through from the dashboard.
- Future HUD/API work should read `/funnels/b1` to populate stream-specific widgets (CTA preview, current copy, etc.).

## Deployment Notes

- Hostnames: In production, route `/funnels/b1/landing` through the public ingress with TLS.
- Tracking: wrap `cta_url` in your preferred analytics (UTM params, affiliate IDs) before shipping.
- Memory: whenever the offer or copy changes significantly, store a note via `store_note` (e.g., `stream:B1`) explaining the rationale and date.

## Next Steps

- Wire revenue logging so every conversion recorded via `scripts/record_revenue.py` can reference this funnel’s identifier (`B1`).
- Add AB testing hooks (duplicate config file per variant) once we have baseline traffic.
