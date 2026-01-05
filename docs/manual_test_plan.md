# Manual Test Plan — God Mode System

Run this checklist after major changes or before opening the system to operators. Steps assume the repo is located at `~/ascentrix`.

## 0. Pre-flight

1. Start the stack with `gmup` (or `docker compose -p godmode up -d`) and wait for `/health` to return `{"ok": true}`.
2. Execute the automated harness:

```bash
chmod +x scripts/full_system_check.sh  # first run only
scripts/full_system_check.sh
```

Resolve any failures before continuing.

## 1. HUD (Web)

1. Open the HUD in a browser (`http://localhost:${GODMODE_HUD_PORT_HOST:-5052}` by default).
2. Verify **Home** widgets populate (metrics, streams, notifications, vault, Blitz status if active).
3. Go to **Streams** and confirm:
   - The business table lists B1–B4.
   - The detail panel shows landing pages and the new **Manage Landing Pages** / **Manage Funnels** buttons.
4. Click **Manage Landing Pages** for B1 or B3:
   - The modal lists the seeded entries (lp_ai-growth-toolkit, lp_content-engine).
   - Open one in Workshop and confirm the HTML renders.
5. Click the new **Manage Funnels** button:
   - The modal loads funnel rows for B1/B3.
   - Creating a funnel succeeds via `/api/businesses/:id/funnels`.
6. Navigate to the **Offers** screen:
   - The offers table lists the seeded “AI Growth Toolkit – Core Offer” and “Content Engine – Starter Offer”.
   - The funnel overview table displays B1 and B3 funnels with “Manage” buttons that reopen the modal.

## 2. Mac Desktop App

1. From `desktop/godmode-desktop`, run `npm start` (or open the built `.app` bundle).
2. Confirm:
   - The embedded HUD loads.
   - Sidebar buttons for Human Queue and Notifications populate using `/api/human/queue` and `/api/notifications`.
   - IPC shortcuts:
     - `open-business-window` creates a dedicated HUD window for a business.
     - `open-blitz-window` loads the Blitz dashboard window.

## 3. Funnels & Offers (API)

1. `curl http://127.0.0.1:${GODMODE_API_PORT_HOST:-5051}/api/offers` → returns the seeded offers with payout windows.
2. `curl http://127.0.0.1:${GODMODE_API_PORT_HOST:-5051}/api/businesses/b1/funnels` → returns the active B1 funnel referencing `lp_ai-growth-toolkit`.
3. `curl http://127.0.0.1:${GODMODE_API_PORT_HOST:-5051}/api/businesses/b3/funnels` → returns the B3 link-in-bio funnel.
4. Optional: POST a new funnel via `/api/businesses/:id/funnels` and confirm it appears in HUD.

## 4. Blitz Mode & Tasks

1. Activate Blitz mode:

```bash
curl -X POST http://127.0.0.1:${GODMODE_API_PORT_HOST:-5051}/api/mode/blitz_all_out_1/activate
```

2. Run the smoke test:

```bash
python scripts/blitz_smoke_test.py
```

   - Confirms at least one funnel-derived opportunity exists.
   - Checks for `blitz_campaign` tasks in `api/tasks/roadmap.jsonl`.
3. Visit `/api/blitz/status` and `/api/blitz/opportunities` to ensure responses contain data.

## 5. Manual Checks & Notes

Use this section to record anything unexpected:

- HUD errors / broken widgets:
- API failures:
- Funnel/landing page rendering issues:
- Blitz mode anomalies:
- Desktop app glitches:

Record issues in `docs/business_readiness.md` or create tasks in `api/tasks/roadmap.jsonl` as needed.
