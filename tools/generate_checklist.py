"""Generate a PDF checklist of repo progress.

This scans markdown files in `design_docs/` and `IMPLEMENTATION_STATUS.md` for markdown
checkboxes ([x] / [ ]) and computes a percentage complete. It will attempt to
use reportlab to produce a PDF; if reportlab isn't installed it will write an
HTML fallback `reports/checklist.html` and exit with a non-zero code.

Usage: python3 tools/generate_checklist.py
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "reports"
OUT_DIR.mkdir(parents=True, exist_ok=True)

MD_FILES = [ROOT / "IMPLEMENTATION_STATUS.md"]
MD_DIR = ROOT / "design_docs"
if MD_DIR.exists():
    MD_FILES += sorted(MD_DIR.glob("*.md"))

checkbox_re = re.compile(r"\[([ xX])\]")
items = []
checked = 0
for p in MD_FILES:
    try:
        txt = p.read_text(encoding="utf-8")
    except Exception:
        continue
    for line in txt.splitlines():
        m = checkbox_re.search(line)
        if m:
            checked |= 0  # noop
            state = m.group(1)
            label = line[m.end():].strip() or p.name
            items.append((state != " ", label))

if items:
    total = len(items)
    done = sum(1 for s, _ in items if s)
    percent = int(done * 100 / total)
else:
    total = 0
    done = 0
    percent = 0

summary = f"Progress: {done}/{total} ({percent}%)"

html_lines = ["<html><body>", f"<h1>Repository Checklist</h1>", f"<h2>{summary}</h2>", "<ul>"]
for s, label in items:
    cls = "done" if s else "todo"
    html_lines.append(f"<li class=\"{cls}\">{'✅' if s else '⬜'} {label}</li>")
html_lines += ["</ul>", "</body></html>"]
html = "\n".join(html_lines)

# Try to render PDF using reportlab if installed
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    out_pdf = OUT_DIR / "checklist.pdf"
    c = canvas.Canvas(str(out_pdf), pagesize=letter)
    w, h = letter
    y = h - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, "Repository Checklist")
    y -= 28
    c.setFont("Helvetica", 12)
    c.drawString(72, y, summary)
    y -= 24
    for s, label in items:
        if y < 72:
            c.showPage()
            y = h - 72
        mark = "✅" if s else "⬜"
        c.drawString(72, y, f"{mark} {label}")
        y -= 18
    c.save()
    print(f"Wrote PDF: {out_pdf}")
except Exception as e:  # fallback: write HTML
    out_html = OUT_DIR / "checklist.html"
    out_html.write_text(html, encoding="utf-8")
    print("Could not generate PDF (reportlab missing). Wrote HTML:", out_html)
    raise
