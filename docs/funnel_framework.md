# Funnel Template Framework Guide

## Purpose

To keep revenue streams consistent and fast to deploy, every funnel references the shared template under `businesses/templates/`. The template captures the canonical section structure (hero, offer, audience, traffic, trust, automation, metrics) so new funnels can be launched by editing JSON instead of inventing layouts from scratch.

## Structure

```
businesses/
  templates/
    funnel_template.json
    sections/
      trust_badge.md
      disclaimer.md
  b1_affiliate_toolkit/
    copy.json
    README.md
  ...
```

- `funnel_template.json` – defines required keys for any funnel. Treat this file as read-only; copy it into a stream folder before editing.
- `sections/` – optional shared markdown snippets (trust badges, disclaimers). Agents can insert these into landing pages or docs.
- Stream folders (B1–B4) store overrides in `copy.json`, plus README instructions and asset placeholders.

## Workflow

1. Copy the template into the new stream folder: `cp businesses/templates/funnel_template.json businesses/bX_new/copy.json`.
2. Update metadata/section fields (hero, offer, etc.) to match the new funnel’s positioning.
3. Upload any creative assets under the stream’s `assets/` folder.
4. Document instructions, KPIs, and integration steps in the stream’s README, linking back to `design_docs/businesses_plan.md`.
5. When autopilot/HUD need to render funnel info, read the stream’s `copy.json` or pipe the data into the API/HUD widgets.

## Current Streams

- `b1_affiliate_toolkit` – AI Growth Toolkit (affiliate/digital product).
- `b2_ecom_holiday` – seasonal ecommerce micro-store.
- `b3_content_engine` – content-driven funnel driving traffic to B1/B2.
- `b4_ai_service` – high-ticket AI service offer.

Each stream incorporates KPIs and automation hooks from the design doc to keep documentation synchronized.

## Next Steps

- Expand the template with additional sections (FAQ, compliance) as funnels mature.
- Build tooling to validate stream `copy.json` files (lint required fields, warn on missing CTA URLs).
- Extend HUD to display key template fields (hero copy, CTA) for each stream detail card.
