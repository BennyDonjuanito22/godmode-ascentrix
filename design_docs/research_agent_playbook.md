# Research Agent Playbook

This playbook tells every builder/researcher agent how to run due diligence, collect data, and translate findings into trusted tasks. Autopilot should reference this file before executing R&D tickets.

## Core Principles
1. **Define the question clearly** – restate the objective, success criteria, and constraints (budget, time, target persona).
2. **Layered sourcing**:
   - Primary: official docs, pricing pages, investor decks.
   - Secondary: analyst blogs, comparison posts, community answers.
   - Tertiary: social chatter (Twitter/Reddit) for qualitative signals.
3. **Triangulate** – never trust a single link. Capture at least two corroborating sources for claims (fees, timelines, conversion data).
4. **Quantify + qualify** – pair numbers (CAGR, CPM, payout) with narrative (why it matters).
5. **Log sources** – every insight gets a markdown bullet and URL so other agents can audit or refresh later.
6. **Produce actionable output** – end each research session with:
   - Snapshot summary (TL;DR).
   - Risks / unknowns.
   - Proposed next steps / tasks to add to roadmap.

## Step-by-step Workflow
1. **Frame** – write a 2–3 sentence research brief at the top of your notes (goal, context).
2. **Seed terms** – list 5–8 keywords/phrases to search (e.g., “Gumroad fee structure 2025”, “AI toolkit marketplaces”).
3. **Source sweep** – for each term:
   - Use `search_repo`, `search_design_docs`, or external web context (if available) to gather links.
   - Save metadata: URL, publish date, key quote/stat.
4. **Evaluate** – score sources for credibility (official = high, forum = medium, random blog = low). Note contradictions.
5. **Synthesize** – group insights under headings (Pricing, Requirements, Demand signals, Competitors).
6. **Recommend** – convert findings into decisions or tasks (e.g., “Add Lemon Squeezy listing after Gumroad due to lower fee”).
7. **Log** – drop summary + source list into `memory/notes.jsonl` (tags `research`, `stream:<id>`).

## Prompt Template (for LLM agents)
```
You are the Research & Development agent for God Mode.
Objective: {goal}
Constraints: {budget/time/market}

Follow this loop:
1. Restate the goal and list hypotheses.
2. Draft search keywords.
3. Gather sources (cite links + credibility).
4. Summarize quantitative + qualitative insights.
5. Recommend concrete next steps/tasks.

Output strictly in JSON:
{
  "goal": "...",
  "hypotheses": [],
  "sources": [{"url": "...", "credibility": "high/med/low", "summary": "..."}],
  "insights": [{"category": "...", "details": "..."}],
  "recommendations": []
}
```

Agents must attach this JSON to their run log and add at least one summary note to memory for continuity.
