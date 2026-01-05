# Password Vault (Temporary Plain-Text Store)

This MVP vault keeps every set of God Mode credentials in one place so agents and operators can grab usernames/passwords without digging through documents or DMs. **It is intentionally simple and currently unencrypted**—treat it as an internal convenience store until we wire a hardened secrets manager.

## API Endpoints

- `GET /vault/credentials` – returns the most recent records (service, username, password, URL, notes).
- `POST /vault/credentials` – create a new record. Body fields:
  - `service` *(required)* – e.g. `"TikTok"`, `"Stripe"`.
  - `username` *(required)*.
  - `password` *(optional)* – omitted → server generates one via `/vault/generate`.
  - `url`, `notes`, `tags` *(optional)*.
- `POST /vault/generate?length=20` – helper for generating strong passwords if you want to copy one before creating the entry.

All routes honor `X-Godmode-Token` if you’ve set `GODMODE_PHONE_TOKEN` for the phone bridge.

## CLI helper (`scripts/store_credential.py`)

Usage:

```bash
python scripts/store_credential.py \
  --service "TikTok" \
  --username ops@godmode.com \
  --password 'Secret123!' \
  --url https://www.tiktok.com/login
```

Flags:

- `--api` (default: `http://127.0.0.1:${GODMODE_API_PORT_HOST:-5051}`) – point at another node or Tailscale URL.
- `--password` omitted + blank at the prompt → auto-generates via `/vault/generate`.

This script should be run immediately after any new account is created so credentials never leave memory/DMs. Autopilot tasks that spawn new accounts should call it via `run_shell`.

## HUD Integration

Home view now includes a “Password Vault” card showing the five most recent entries with copy buttons for username and password (uses the browser clipboard API). Use this to grab details quickly from a Mac/iPad/iPhone session.

## Roadmap / Security Notes

- Secrets are currently stored in `data/password_vault.jsonl` in plain text. Once budget allows, migrate to an encrypted store (1Password Connect, AWS Secrets Manager, Hashicorp Vault, etc.).
- Add per-entry encryption + masking before exposing the list outside the LAN.
- Wire alerts (missing entry detection) for autopilot account creation tasks.

---

## Credential Dump – 2025-12-05

> **Reminder:** All accounts below were created as operational sandboxes. Treat them as burner assets and rotate passwords once the hardened vault ships. Unless explicitly noted, assume the recovery phone is (407) 385‑8390.

### Instagram (business use only)

| Label | Username / Handle | Password | Email | Notes |
| --- | --- | --- | --- | --- |
| Real Talk Media | `real_talk_media` | `MicroFrenched0422@` | `Autopilot.TikTok.1@gmail.com` | No links to personal IG. |
| Te Amo Mi Amor | `143_miamor` | `MicroFrenched0422@` | `Autopilot.TikTok.2@gmail.com` | Username locked until Jan 4 2025. |
| Brat.Fashion | `bratgirlsummer.collective` | `MicroFrenched0422@` | `Autopilot.TikTok.3@gmail.com` | Username locked until Jan 4 2025. |
| Puppies Over People | `puppies_over_people` | `MicroFrenched0422@` | `Autopilot.TikTok.4@gmail.com` |  |
| Owl (demo) | `owl.4634591` | `MicroFrenched0422@` | `Autopilot.TikTok.5@gmail.com` |  |
| Trendsetter Beauty | `TrendSetter.Beauty` | `MicroFrenched0422@` | `Autopilot.TikTok.6@gmail.com` |  |
| Trendy Hair Inspo | `trendy.hair.inspo` | `MicroFrenched0422@` | `Autopilot.TikTok.7@gmail.com` |  |
| Rhino Demo | `rhino.2739991` | `MicroFrenched0422@` | `Autopilot.TikTok.8@gmail.com` |  |
| Dolphin Demo | `dolphin.8872030` | `MicroFrenched0422@` | `Autopilot.TikTok.9@gmail.com` |  |
| Dragon Demo | `dragon.6270961` | `MicroFrenched0422@` | `Autopilot.TikTok.10@gmail.com` |  |

### Gmail / TikTok / YouTube bundles

| Label | Email / Username | Password | Notes |
| --- | --- | --- | --- |
| Autopilot TikTok 1 | `Autopilot.TikTok.1@gmail.com` | `MicroFrenched0422@` | TikTok/YT access aligned to IG #1. |
| Autopilot TikTok 2 | `Autopilot.TikTok.2@gmail.com` | `MicroFrenched0422@` | Username locked until Jan 4 2025. Avoid publishing until then. |
| Autopilot TikTok 3 | `Autopilot.TikTok.3@gmail.com` | `MicroFrenched0422@` | Username locked until Jan 4 2025. |
| Autopilot TikTok 4 | `Autopilot.TikTok.4@gmail.com` | `MicroFrenched0422@` |  |
| Autopilot TikTok 5 | `Autopilot.TikTok.5@gmail.com` | `MicroFrenched0422@` |  |
| Autopilot TikTok 6 | `Autopilot.TikTok.6@gmail.com` | `MicroFrenched0422@` |  |
| Autopilot TikTok 7 | `Autopilot.TikTok.7@gmail.com` | `MicroFrenched0422@` |  |
| Autopilot TikTok 8 | `Autopilot.TikTok.8@gmail.com` | `MicroFrenched0422@` |  |
| Autopilot TikTok 9 | `Autopilot.TikTok.9@gmail.com` | `MicroFrenched0422@` |  |
| Trendsetter Beauty | `Autopilot.TikTok.10@gmail.com` | `MicroFrenched0422@` | Matches IG “Trendsetter Beauty”. |

### Personal (use only on direct request)

| Platform | Username / Email | Password | Notes |
| --- | --- | --- | --- |
| Instagram | `Schaefer_Ian` | `MicroFrenched0422@` | Only for direct personal requests from Ian. |
| Facebook | `ianschaefer7@gmail.com` | `MicroFrenched0422@` | Personal FB. |
| TikTok | `@schaefer_ian` | `MicroFrenched0422@` | Recovery phone `402-981-6702`. |

### Affiliate / Storefront Platforms

| Service | Username / Email | Password | Notes |
| --- | --- | --- | --- |
| Digistore24 | `ascendrixventuresllc@gmail.com` | `MicroFrenched0422@` |  |
| Gumroad | `ascendrixventuresllc@gmail.com` | `MicroFrenched0422@` | CTA already points to instant pay. |
| ClickBank | `Autopilot.TikTok.1@gmail.com` | `MicroFrenched0422@!` | Note the `!` suffix. |
| WarriorPlus | `AscendrixVentures` / `ascendrixventuresllc@gmail.com` | `MicroFrenched0422@` |  |
| JVZoo | `ascendrixventuresllc@gmail.com` | `MicroFrenched0422@` |  |
| Payhip | `ascendrixventuresllc@gmail.com` | `MicroFrenched0422@` |  |
| Lemon Squeezy | Store “Ascendrix Ventures” / `ascendrixventuresllc@gmail.com` | `MicroFrenched0422@` |  |
| Shopify | `autopilot.tiktok.1@gmail.com` | *(set during signup)* | Need new store request (see below). |
| Sellfy | `ascendrixventuresllc@gmail.com` | `MicroFrenched0422@` | Free trial activated 12/5/25 4:55 PM. |
| Namecheap | `schaeferunlimited` / `schaeferunlimitedllc@gmail.com` | `FrenchedForever0422@` | Domain registrar. |

### Shopify – New Account Request Message

```
Subject: Request to Spin Up New Shopify Store (Ascendrix Ventures)

Hi Shopify Support,

We are ready to launch a fresh Shopify store under Ascendrix Ventures using the operator email autopilot.tiktok.1@gmail.com. Please confirm the best next steps to:
1. Activate a brand new storefront tied to that email.
2. Enable instant payout testing (Stripe/PayPal) on the store from day one.
3. Ensure the account is cleared for multiple collaborator logins so our automation agents can manage listings and payouts.

Let us know if you need any additional verification or documentation. We’d like to complete setup today so we can push our AI Growth Toolkit launch through Shopify alongside Gumroad/Lemon Squeezy.

Thanks!
— The God Mode Ops Team
```

> Send the above through Shopify support chat/email once we’re ready to provision the new store. Update this doc with the assigned store URL + admin credentials afterward.
