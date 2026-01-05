# God Mode Launch & Test Checklist

## Step 1 – Start the stack
1. Run `gmup` (or `docker compose up`) from the repo root.
2. Wait for all containers to show **healthy**, including `godmode-api-1`.
3. If any service restarts, inspect logs (`docker logs <service>`) before proceeding.

## Step 2 – Automated full-system check
1. Ensure Docker is still running.
2. Execute `./scripts/full_system_check.sh` from the repo root.
3. Confirm the script reports success for:
   - Backend health tests (`tests/test_health_endpoints.py`).
   - HUD build (`npm --prefix hud run build`).
   - macOS desktop build (`npm --prefix desktop/godmode-desktop run build:mac`).

## Step 3 – HUD smoke test
1. Open the HUD in a browser at `http://localhost:${GODMODE_HUD_PORT_HOST:-5052}` (or your remote URL).
2. Navigate to:
   - `/` (home dashboard).
   - `/businesses/<slug>` for each active business.
   - Landing page editors (`/businesses/<slug>/landing-pages`).
   - Blitz dashboard (`/#/blitz/dashboard`).
3. Verify data loads without console errors.

## Step 4 – Mac desktop app
1. Development run: `cd desktop/godmode-desktop && npm start`.
   - Confirm the window loads and HUD content is reachable.
2. Packaged run: after the build step above, open `desktop/godmode-desktop/dist/*.dmg` and install the app.
3. Verify the Quantum AI icon appears in the dock and multi-window shortcuts work.

## Step 5 – iPhone Control app
1. `cd mobile/godmode-phone && xcodegen generate` (if the workspace isn’t generated yet).
2. Open the workspace in Xcode and select the **GodModeControl** target.
3. Set `API_BASE_URL` / Settings tab to point at the running API (e.g., `http://localhost:${GODMODE_API_PORT_HOST:-5051}` or Tailscale URL).
4. Build & run on a device (Cmd+R). Validate:
   - Human Queue view hits `/api/human/queue`.
   - Notifications tab hits `/api/notifications`.
   - Blitz/Status views hit `/api/blitz/status`.

## Step 6 – Optional Blitz smoke test
1. Activate Blitz mode via `scripts/mode_control.py --set blitz`.
2. Hit `/api/blitz/status` and confirm totals update.
3. Check HUD + desktop + phone client all display Blitz metrics consistently.

## Step 7 – Sign-off
- Capture screenshots of HUD, desktop app, and iPhone client.
- Log completion in `logs/launch_checklist.log` or your ops tracker.
- Proceed to manual QA or launch campaign as scheduled.
