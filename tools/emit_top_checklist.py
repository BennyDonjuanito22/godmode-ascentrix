from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TOP_TASKS = [
    "Launch API locally with Ollama (local-first LLM)",
    "Make OpenAI/ChatGPT mode switchable and optional",
    "Generate PDF checklist of repo progress",
    "Start and verify API health endpoint (/health)",
    "Run autopilot smoke-run in local mode and reset state",
]

html_lines = ["<html><body>", "<h1>Top 5 Tasks</h1>", "<ul>"]
for t in TOP_TASKS:
    html_lines.append(f"<li>⬜ {t}</li>")
html_lines += ["</ul>", "</body></html>"]
html = "\n".join(html_lines)

out_html = OUT_DIR / "checklist_top.html"
out_html.write_text(html, encoding="utf-8")
print(f"Wrote HTML: {out_html}")

# Try PDF
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    out_pdf = OUT_DIR / "checklist_top.pdf"
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    w, h = letter
    y = h - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, "Top 5 Tasks")
    y -= 28
    c.setFont("Helvetica", 12)
    for t in TOP_TASKS:
        if y < 72:
            c.showPage()
            y = h - 72
        c.drawString(72, y, f"⬜ {t}")
        y -= 18
    c.save()
    print(f"Wrote PDF: {out_pdf}")
except Exception:
    print("reportlab not available; wrote HTML only")
