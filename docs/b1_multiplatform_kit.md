# B1 Multi-Platform Listing Kit

Use this kit whenever we clone the AI Growth Toolkit onto a new marketplace. Everything here is modular—copy blocks, pricing guidance, image specs, and UTM templates—so Autopilot can fill in the blanks and publish without reinventing the funnel.

---

## Core Offer Snapshot

- **Product name:** AI Growth Toolkit
- **Tagline:** “Ship AI-powered funnels in days, not months.”
- **Deliverables:** 30+ Notion dashboards, prompt packs (shorts, email, outreach, nurture), autopilot launch checklist, revenue logging scripts, partner outreach templates.
- **Ideal buyers:** Solopreneurs, creator agencies, automation freelancers.
- **Proof point:** Built and used internally to run the God Mode stack (HUD + Autopilot). Weekend build → $200/day case study.

---

## Copy Blocks

### Hero Description (150–200 words)
```
Stop rebuilding the same AI funnel every week. The AI Growth Toolkit hands you the exact Notion dashboards, prompt packs, and SOPs we use in our own automation lab. Drop your offer into the templates, point your agent/autopilot at the launch checklist, and let it execute end-to-end: landing page copy, short-form hooks, partner outreach, revenue logging, and nurture.
- 30+ plug-and-play Notion dashboards (funnels, content, finance, partner CRM)
- Prompt packs for TikTok/Shorts, LinkedIn, email, affiliate pitches, nurture
- Autopilot-ready roadmap with guardrails + scripts (record_revenue, nurture_leads)
Duplicate the workspace, customize the CTA link, and ship. Founder price is limited—future updates are included.
```

### Bullet Highlights
- Build once, clone everywhere: Notion + SOP stack used inside God Mode.
- Prompt packs for every channel (short-form, email, partner outreach, nurture).
- Autopilot-ready launch checklist with guardrails + scripts.
- Includes lead capture + ledger automations (scripts/record_revenue.py, nurture_leads.py).
- Lifetime updates + partner outreach templates.

### FAQ Snippets
- **Does this work if I don’t have a product?** Yes—swap in any affiliate offer or use our included AI service template.
- **Is it compatible with Gumroad/Lemon Squeezy/etc.?** Yep. Dup the workspace, update the CTA URL, and follow the listing checklist below.
- **Can my AI agent run the launch automatically?** That’s the point. The roadmap + guardrails were written for Autopilot (or any tool-wielding agent).

---

## Pricing & Offer Structure

| Platform          | Suggested Price | Notes                                                  |
| ----------------- | --------------- | ------------------------------------------------------ |
| Gumroad           | $67 (founder tier) | Use pay-what-you-want floor $37 for urgency tests.     |
| Lemon Squeezy     | $79              | Higher perceived value; highlight lifetime updates.     |
| Etsy (digital)    | $47              | Compete with templates; upsell email support add-on.    |
| AppSumo/G2/etc.   | $99–129          | Bundle “Launch Concierge Call” (30 min) as bonus.       |

- **Cross-platform rule:** keep a single Stripe/PayPal backend link for refunds -> easier ledger reconciliation.
- **Urgency script:** “Founder price ends once we hit 200 operators. Lifetime updates included.”

---

## Image / Media Specs

| Asset             | Dimensions      | Content                                                                 |
| ----------------- | --------------- | ------------------------------------------------------------------------ |
| Cover mockup      | 3000x2000 PNG   | Toolkit dashboard hero + short-form prompt previews.                     |
| Gallery slide #1  | 1920x1080 PNG   | Notion workspace screenshot (HUD + roadmap).                             |
| Gallery slide #2  | 1920x1080 PNG   | Prompt pack excerpts + autopilot logs.                                   |
| Gallery slide #3  | 1920x1080 PNG   | Lead capture + ledger automation illustration.                           |
| Bonus image       | 1080x1920 JPG   | Short-form hooks as text overlay (reuse for TikTok/Shorts).              |

Render PSD/FIG files once; export per marketplace requirements (JPG under 2MB for Etsy, PNG with transparent background for Gumroad).

---

## Listing Checklist (per platform)

1. Duplicate `config/funnels/b1.json` and update CTA URL with marketplace link.
2. Export latest landing hero copy + bullets from this kit.
3. Upload cover + gallery assets (see spec table).
4. Paste hero description + bullet highlights.
5. Add FAQ block + support contact (`support@godmodeops.com`).
6. Add bonus files:
   - `docs/revenue_funnel_1.pdf` (export from repo).
   - `content/output/b1/shorts/20251130_wave1.md` (rename “Short-form Hooks Pack”).
7. Set price + coupon/discount rules.
8. Update `docs/b1_promo_log.md` with new listing link.
9. Run `python3 scripts/nurture_leads.py send --limit 25` to hit new leads from that marketplace.

---

## UTM / Tracking Templates

Use consistent tagging for analytics + ledger entries.

| Channel      | Base URL                              |
| ------------ | ------------------------------------- |
| Website CTA  | `https://buy.stripe.com/...`          |
| Gumroad      | `https://godmode.gumroad.com/...`     |
| Lemon Squeezy| `https://godmode.lemonsqueezy.com/...`|
| Etsy         | `https://www.etsy.com/listing/...`    |

### UTM format
```
?utm_source={platform}&utm_medium=marketplace&utm_campaign=b1_toolkit&utm_content={variant}
```

Examples:
- Gumroad: `...?utm_source=gumroad&utm_medium=marketplace&utm_campaign=b1_toolkit&utm_content=cover`
- Lemon Squeezy partner link: `...?utm_source=lemonsqueezy&utm_medium=affiliate&utm_campaign=b1_toolkit&utm_content=partner_aff001`

Log each new UTM variant in `docs/b1_promo_log.md` and `memory/notes.jsonl` (tags `stream:B1`, `utm`).

---

## Files & Automations to Include

- `/content/output/b1/*` – short-form hooks, email copy, LinkedIn post template.
- `/scripts/nurture_leads.py` – highlight CLI usage in listing (value add).
- `/scripts/record_revenue.py` – mention ledger automation every marketplace listing.
- `/docs/security_infra_audit_YYYYMMDD.md` – optional trust signal.

Package release ZIP includes:
```
├── README.md (setup instructions)
├── Notion workspace export (.zip)
├── Prompt packs (.md/.txt)
├── Scripts (record_revenue.py, nurture_leads.py)
├── Bonus assets (hooks, outreach templates)
```

---

## Future Enhancements

- Auto-generate marketplace descriptions from this kit using `run_agent` template.
- Maintain a changelog section so each listing shows “What’s new” (helps with AppSumo/G2 trust).
- Add video walkthrough (Loom) per platform to boost conversion.
