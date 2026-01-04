# Funnel Template Framework

This directory contains reusable assets each revenue stream (B1–B4) can clone or extend. The goal is to keep every funnel consistent—one place for copy blocks, layout JSON, automation scripts, and deployment notes—so agents can launch or modify funnels without reinventing structure.

## Template Layout

```
businesses/
  templates/
    funnel_template.json         # canonical structure
    sections/                    # optional shared copy blocks
    assets/                      # shared imagery/icons
  b1_affiliate_toolkit/          # stream-specific folder
  b2_ecom_holiday/
  b3_content_engine/
  b4_ai_service/
```

- `funnel_template.json` – defines the sections each funnel must describe (hero, offer, proof, traffic, automation).
- `sections/` – optional Markdown snippets (e.g., trust badges, disclaimers) that multiple funnels can include.
- `assets/` – placeholder imagery/icons to ensure landing pages share a visual language.

## Stream Folders

Each stream folder (e.g., `b1_affiliate_toolkit/`) mirrors the template keys:

- `copy.json` – overrides to `funnel_template.json`.
- `assets/` – stream-specific screenshots/mockups.
- `README.md` – instructions + KPIs for that funnel, linking back to `design_docs/businesses_plan.md`.
- `notes/` – optional logs or data extracted from `memory/notes.jsonl`.

Agents should always start by copying the template:

```bash
cp -r businesses/templates/funnel_template.json businesses/bX_new_funnel/copy.json
```

Then edit `copy.json` + assets to match the new offer.
