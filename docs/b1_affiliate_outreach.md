# B1 Affiliate / Partner Outreach Playbook

Use this doc to systematize the “close warm partners” task. Every outreach touchpoint should create a corresponding lead (for tracking) and a note in `memory/notes.jsonl`.

## Target Partner Shortlist

| Partner | Audience | Pitch Angle | Contact Info |
| --- | --- | --- | --- |
| Creator Hooks Newsletter | Daily growth marketers | Showcase toolkit as a done-for-you prompt pack they can resell | hi@creatorhooks.com |
| Indie Maker Twitter Spaces | Bootstrappers + nocoders | Offer exclusive space + toolkit bundle | DM @indiemakers |
| TikTok “AI tools” Creators | Short-form reviewers | Give them unique discount/UTM to earn rev share | DM via TikTok |
| LinkedIn Ghostwriters | Service providers | Toolkit becomes their onboarding upsell | Email from LinkedIn profile |

Add more partners as you discover them; store structured details in `memory/notes.jsonl` (tags `stream:B1`, `partner`).

## Outreach Template (DM / Email)

```
Subject: Toolkit collab for your audience?

Hey {{name}},

I run the AI Growth Toolkit — the Notion + prompt stack our automation system uses.
Your audience is building the same thing from scratch every week.

I'd love to give you:
• 40% rev share via your custom Stripe link
• Early drop content you can repurpose
• Callouts inside the HUD + promos

Demo + checkout: https://godmode.gumroad.com/l/aigrowthtoolkit
Affiliate tracking: https://127.0.0.1:5051/funnels/b1/lead?tag={{partner_code}}

If it's a fit I'll spin up your assets in under a day.
- Ascentrix
```

## Tracking + Next Actions

1. When you send an outreach message, add a lead with `source="affiliate"` and `tag="partner:NAME"` via `POST /funnels/b1/lead` or the landing form (`?utm_source=partner.NAME`).
2. Update `docs/b1_promo_log.md` once a partner publishes your asset.
3. If a partner converts, run `python scripts/nurture_leads.py convert --email <partner@email> --amount ... --source affiliate`.
4. Record any negotiated rev-share terms in `memory/notes.jsonl` so future operators know the split.
5. Review partner performance weekly and prune the ones that don’t move revenue.

## Current Outreach Status (Wave 1)

| Partner | Platform | Affiliate ID | Tracking URL | Status | Next Step |
| --- | --- | --- | --- | --- | --- |
| Alice Johnson | Twitter (AI creator) | aff001 | https://godmode.gumroad.com/l/aigrowthtoolkit?aff=aff001 | Sent 2025-11-30 | Await reply, follow up in 48h |
| Ben Thompson | Newsletter (growth marketing) | aff002 | https://godmode.gumroad.com/l/aigrowthtoolkit?aff=aff002 | Sent 2025-11-30 | Offer Loom walkthrough |
| Cara Lee | TikTok (automation tips) | aff003 | https://godmode.gumroad.com/l/aigrowthtoolkit?aff=aff003 | Sent 2025-11-30 | Share short-form assets once she responds |
| David Kim | Newsletter (AI founders) | aff004 | https://godmode.gumroad.com/l/aigrowthtoolkit?aff=aff004 | Sent 2025-11-30 | Send performance stats after first sales |
| Emma Garcia | Twitter (creator ops) | aff005 | https://godmode.gumroad.com/l/aigrowthtoolkit?aff=aff005 | Sent 2025-11-30 | DM follow-up if no reply in 3 days |

All outreach JSONL entries live in `memory/notes.jsonl` (tags: `stream:B1`, `partner`). Use `python scripts/nurture_leads.py send --limit N` to deliver updates to any partner who opts into the lead capture form.
