"""Funnel configuration helpers for the revenue streams."""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field
import os
from pathlib import Path
from typing import Any, Dict, List

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR.parent / "config" / "funnels" / "b1.json"


@dataclass
class B1FunnelConfig:
    hero_title: str = "Unlock the AI Growth Toolkit"
    hero_subtitle: str = "Plug-and-play prompts, SOPs, and automations to spin up revenue in days, not months."
    bullets: List[str] = field(
        default_factory=lambda: [
            "20+ Notion templates for content, funnels, and ops",
            "Battle-tested prompt packs for short-form and sales flows",
            "Step-by-step launch checklist that God Mode follows internally",
        ]
    )
    proof: str = "“This toolkit turned my scattered ideas into a tangible funnel within a weekend.” – Placeholder Creator"
    cta_label: str = "Get Early Access"
    cta_url: str = "https://example.com/replace-with-affiliate-or-product-link"
    testimonial_label: str = "Next cohort ships in under 7 days"
    fine_print: str = "Placeholder offer. Replace CTA URL and copy in config/funnels/b1.json."

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _apply_env_overrides(config: B1FunnelConfig) -> B1FunnelConfig:
    """Allow operators to override CTA details via environment variables."""
    cta_url = os.environ.get("B1_CTA_URL") or os.environ.get("GODMODE_B1_CTA_URL")
    if cta_url:
        config.cta_url = cta_url.strip()
    cta_label = os.environ.get("B1_CTA_LABEL")
    if cta_label:
        config.cta_label = cta_label.strip()
    return config


def load_b1_funnel_config() -> B1FunnelConfig:
    if CONFIG_PATH.is_file():
        try:
            data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            return _apply_env_overrides(B1FunnelConfig(**data))
        except Exception:
            # Fall back to defaults if the file is malformed.
            pass
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.exists():
        CONFIG_PATH.write_text(json.dumps(B1FunnelConfig().to_dict(), indent=2), encoding="utf-8")
    return _apply_env_overrides(B1FunnelConfig())


def render_b1_landing(config: B1FunnelConfig) -> str:
    bullets_html = "".join(f"<li>{line}</li>" for line in config.bullets)
    return f"""
<!doctype html>
<meta charset="utf-8">
<title>AI Growth Toolkit – Placeholder</title>
<style>
body {{
  font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, sans-serif;
  margin:0;
  background:#050b18;
  color:#e2e8f0;
}}
.hero {{
  max-width:720px;
  margin:0 auto;
  padding:80px 20px;
  text-align:center;
}}
h1 {{
  font-size:42px;
  margin-bottom:18px;
  color:#bfdbfe;
}}
p {{
  font-size:18px;
  line-height:1.5;
  color:#cbd5f5;
}}
ul {{
  list-style:none;
  padding:0;
  margin:30px 0;
}}
li {{
  margin:12px 0;
  padding-left:18px;
  position:relative;
}}
li::before {{
  content:'➤';
  position:absolute;
  left:0;
  color:#38bdf8;
}}
.cta {{
  display:inline-flex;
  margin-top:20px;
  padding:14px 30px;
  border-radius:999px;
  background:#2563eb;
  color:#f8fafc;
  text-decoration:none;
  font-weight:600;
}}
.lead-card {{
  margin-top:30px;
  padding:24px;
  border-radius:16px;
  background:#0f172a;
  border:1px solid rgba(148,163,184,.3);
  text-align:left;
}}
.lead-card label {{
  display:block;
  font-size:13px;
  color:#a5b4fc;
  margin-bottom:6px;
}}
.lead-card input {{
  width:100%;
  padding:10px 14px;
  border-radius:999px;
  border:1px solid rgba(148,163,184,.4);
  background:rgba(15,23,42,.6);
  color:#f8fafc;
  margin-bottom:12px;
}}
.lead-card button {{
  width:100%;
  padding:12px;
  border-radius:999px;
  border:none;
  background:#38bdf8;
  color:#0f172a;
  font-weight:600;
  cursor:pointer;
}}
.lead-card small {{
  display:block;
  margin-top:10px;
  color:#94a3b8;
}}
.flash {{
  margin-top:12px;
  font-size:14px;
}}
.flash.ok {{ color:#34d399; }}
.flash.err {{ color:#f87171; }}
.badge {{
  display:inline-block;
  margin-top:20px;
  padding:6px 12px;
  border-radius:12px;
  background:#1e293b;
  color:#93c5fd;
  font-size:14px;
}}
.proof {{
  margin-top:30px;
  font-style:italic;
  color:#e0f2fe;
}}
.fine-print {{
  margin-top:60px;
  font-size:13px;
  color:#94a3b8;
}}
</style>
<body>
  <section class="hero">
    <h1>{config.hero_title}</h1>
    <p>{config.hero_subtitle}</p>
    <ul>{bullets_html}</ul>
    <a class="cta" href="{config.cta_url}" target="_blank" rel="noopener noreferrer">{config.cta_label}</a>
    <div class="badge">{config.testimonial_label}</div>
    <div class="proof">{config.proof}</div>
    <div class="fine-print">{config.fine_print}</div>
    <div class="lead-card">
      <h3 style="margin-top:0;">Want the launch checklist sent to your inbox?</h3>
      <form id="lead-form">
        <label for="lead-email">Email address</label>
        <input id="lead-email" name="email" type="email" placeholder="you@example.com" required>
        <button type="submit">Send the follow-up</button>
        <small>We’ll send one playbook email and only follow up when new drops land.</small>
      </form>
      <div id="lead-flash" class="flash" role="status"></div>
    </div>
  </section>
  <script>
  const leadForm = document.getElementById("lead-form");
  const leadFlash = document.getElementById("lead-flash");
  const params = new URLSearchParams(window.location.search);
  const sourceTag = params.get("utm_source") || params.get("source") || "landing";

  leadForm.addEventListener("submit", async (event) => {{
    event.preventDefault();
    leadFlash.textContent = "Saving your spot…";
    leadFlash.className = "flash";
    const email = document.getElementById("lead-email").value.trim();
    try {{
      const response = await fetch("/funnels/b1/lead", {{
        method: "POST",
        headers: {{"Content-Type": "application/json"}},
        body: JSON.stringify({{email, source: sourceTag}})
      }});
      if (!response.ok) throw new Error("Request failed");
      leadFlash.textContent = "Thanks! Check your inbox for the toolkit instructions.";
      leadFlash.className = "flash ok";
      leadForm.reset();
    }} catch (err) {{
      leadFlash.textContent = "Could not save your email. Please try again.";
      leadFlash.className = "flash err";
    }}
  }});
  </script>
</body>
"""
