# B1 Promo Sprint (48-Hour Blitz)

## Objective
Drive a spike of conversions for the AI Growth Toolkit by saturating short-form channels and outreach touchpoints over a 48-hour window (extendable to 72 hours when momentum is strong).

## Timeline

| Time | Action |
| --- | --- |
| H-24 | Prep assets (3 hero hooks, 2 testimonial variants, CTA overlays). |
| H-12 | Queue teaser content (TikTok, IG Reels, YT Shorts, Twitter). |
| H0 | Launch blitz: publish first wave, update link-in-bio with UTM tracker. |
| H+12 | Release social proof clip + behind-the-scenes demo. |
| H+24 | Run live AMA / Twitter Space linking to CTA. |
| H+36 | Share “last chance” reminder and email follow-up. |
| H+48 | Publish recap, log performance, and pivot to nurture. |
| H+60 | Share behind-the-scenes build thread + nurture reminder. |
| H+72 | Drop partner shout-outs, archive assets in `content/output/b1/`, and queue the next sprint. |

## Hooks & Angles

1. “The AI playbook I used to build a $200/day system in a weekend.”
2. “Steal my entire Notion + prompt stack (no upsell at the end).”
3. “Before/after: chaos spreadsheets vs. the toolkit checklist.”

## Content Checklist

- Short-form scripts (store under `content/output/b1/`).
- Carousel/Thread summarizing toolkit deliverables.
- Testimonial card (placeholder until real proof arrives).
- Email template (teaser + last-chance).
- Outreach DM template for warm leads.

## Execution Checklist

- [ ] Record a Loom walk-through of the toolkit (embed short clips across socials).
- [ ] Export TikTok/Shorts clips into `content/output/b1/shorts/` with filenames `YYYYMMDD_hook.mp4`.
- [ ] Update `docs/b1_promo_log.md` (new file) with URLs, publish times, and measured CTR for each asset.
- [ ] After every wave, run `python scripts/nurture_leads.py send --limit 25` to hit new subscribers immediately.
- [ ] When sales arrive, run `python scripts/nurture_leads.py convert --email ...` so ledger entries stay in sync.

## Metrics to Watch

- Ledger entries tagged `B1` (use `scripts/record_revenue.py`).
- Bio link CTR (via UTM tracking).
- Short-form views/save rate.
- Newsletter opt-ins (if offering lead magnet).

## Post-Sprint

1. Log results + lessons in `memory/notes.jsonl` (tags `stream:B1`, `promo`).
2. Update `businesses/b1_affiliate_toolkit/` assets with winning copy.
3. Append final stats + learnings to `docs/b1_promo_log.md`.
4. Schedule the next promo slot (bi-weekly cadence recommended) and refresh affiliate pitches (see `docs/b1_affiliate_outreach.md`).
