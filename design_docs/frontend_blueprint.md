# God Mode Frontend Blueprint – iPhone First

## Vision

Deliver a flagship AI command center that feels native to iPhone/iPad, scales to macOS, and eventually mirrors onto desktop/web. The app must combine:

1. Conversational assistant (text, voice, avatar) with persistent transcripts.
2. Live collaboration surfaces (screen sharing, file drop/editing, media previews).
3. Automation console for executing tasks (emails, campaigns, ecommerce ops).
4. Memory recall and search (timeline, tagged notes, location/time metadata).

The experience should match or exceed ChatGPT “Pro” quality, while integrating directly with God Mode’s backend (HUD APIs, ledger, vector memory, agents).

## Platform Choices

- **Primary:** SwiftUI + Combine for iOS/iPadOS/macOS (Catalyst or SwiftUI multiplatform). Swift + native frameworks for AV, screen sharing (ReplayKit), FaceTime-style calls (CallKit, WebRTC).
- **Secondary:** React Native or Flutter prototypes only if cross-platform speed becomes more important later.
- **Backend connectivity:** REST + WebSockets to existing `/hud/*`, `/finance/*`, `/memory/*`, `/tasks/*` endpoints. Future gRPC/WebRTC channels for real-time agents.

## Core Modules

1. **Home Dashboard**
   - Live snapshot widgets: revenue, tasks, autopilot status, memory highlights.
   - Alerts feed: security warnings, ledger anomalies, agent failures.
   - Quick actions: “Launch promotion”, “Record revenue”, “Ask agent…”.
2. **Conversation Hub**
   - Chat interface with text/voice input (Speech framework) and optional avatar (2D/3D) for face-to-face talk.
   - Toggle between text transcripts and “Avatar mode” (WebRTC feed or local render).
   - Conversations tagged by topic, location, participants; transcripts searchable with filters.
   - After each call/chat, app stores summary + location/time metadata via backend memory APIs.
3. **Commands & Automations**
   - Task composer: natural-language prompt + structured forms for email, SMS, ad campaigns, ecommerce sourcing.
   - Tool permission layer: confirm before sending emails/texts or editing files; show diff preview.
   - Execution log showing each agent/tool step with success/failure statuses.
4. **Live Collaboration**
   - Screen sharing using ReplayKit + WebRTC; remote control requests queue to backend.
   - Media inbox for photos/videos/voice memos; app can view/edit (Core Image/AVFoundation) then sync edits to backend.
   - Whiteboard/annotation mode for planning sessions.
5. **Memory & Timeline**
   - Searchable timeline of interactions (chat, calls, tasks, ledger events) with filters (tags, location, people).
   - Timeline entries link to underlying notes (`memory/notes.jsonl`), tasks, or files.
   - “Memory cards” highlight key learnings, pinned insights, or open loops.
6. **Settings & Profiles**
   - Account management, API keys (if user runs own nodes), notification preferences.
   - Security center: device trust, active sessions, biometric unlock toggle.
   - Meeting cadence reminders (weekly security, bi-weekly product, monthly strategy).

## Experience Goals

- **Natural conversation:** voice-first, quick context recall, avatar presence (robot/persona) for visual engagement.
- **Command center layout:** multi-pane design (dashboard + chat + tasks) on iPad/Mac; tabbed navigation on iPhone.
- **Assistive logging:** after each interaction, app auto-summarizes conversation + location/time so future recall is effortless.
- **Media-friendly:** seamless photo/video/voice capture and editing, with AI suggestions and automation hooks.
- **Trust & safety:** clear confirmation steps before any outbound action; audit trail viewable in the app.

## Technical Footprint

- Networking: Combine or async/await wrappers around `URLSession` hitting `/hud/*`, `/finance/*`, `/memory/*`, `/tasks`.
- Real-time updates: WebSockets (Starscream) or native `URLSessionWebSocketTask` for agent events, autopilot status, screen-sharing control messages.
- Media: ReplayKit + WebRTC (via open-source libs) for screen sharing; AVFoundation for voice/video capture; VisionKit for scanning documents.
- Storage: Local Core Data/Realm cache for offline transcripts; encrypted keychain for auth tokens.
- Authentication: OAuth/token exchange with backend; Face ID/Touch ID for unlocking the app.
- Notifications: Push notifications for alerts, meeting reminders, task completions.

## Integration Points w/ Backend

- `/hud/home` etc. supply dashboard data (revenue/tasks/alerts).
- `/memory/search`, `/memory/ingest` power timeline and recall.
- `/finance/ledger` for revenue capture/inbox.
- `/tasks/roadmap.jsonl` interface (via new REST wrapper) for viewing/creating tasks.
- `/funnels/*` endpoints for B1/B2/B3 content preview and editing.
- New endpoints needed:
  - `/agents/converse` for real-time chat/voice sessions.
  - `/media/upload` for photo/video/audio handling.
  - `/automation/execute` for structured actions (email, SMS, ad ops).
  - `/presence` for avatar state and meeting invites.

## Security/Privacy Considerations

- All communications encrypted (TLS). ReplayKit/WebRTC sessions require secure signaling (via backend) and optional end-to-end encryption.
- Action confirmations logged; user can review/undo tasks.
- Option to run against self-hosted backend (Mac mini) with local network access only.
- Strict permission prompts for screen sharing, camera/mic, photo library.

## Roadmap (Frontend Workstream)

1. **Phase A – Foundation**
   - SwiftUI project setup, app shell, auth flow, API client.
   - Home dashboard pulling `/hud/home`.
   - Basic chat view with transcripts (text-only).
2. **Phase B – Voice & Avatar**
   - Integrate speech-to-text, text-to-speech.
   - Avatar mode (initially 2D animation + audio; later WebRTC video avatar).
3. **Phase C – Automations & Tools**
   - Command composer, tool permission UI, execution logs tied to backend agents.
4. **Phase D – Collaboration & Media**
   - Screen sharing (ReplayKit + WebRTC), media inbox/editor.
   - Timeline/memory cards with search and tagging.
5. **Phase E – Cross-platform**
   - macOS Catalyst build, iPad multi-pane enhancements, eventual web/Electron port.

## Next Steps

- Define detailed UI flows/wireframes for Home, Conversation, Automations, Collaboration, Timeline, Settings.
- Coordinate with backend to expose new endpoints for conversation sessions, media upload, and automation control.
- Create a component library (SwiftUI) to ensure consistent UI across tabs/panes.
- Add tasks in `api/tasks/roadmap.jsonl` for each frontend milestone so autopilot can help with scaffolding, endpoint work, and documentation.
