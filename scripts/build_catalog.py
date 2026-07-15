#!/usr/bin/env python3
"""Build the faculty-facing skill catalog (docs/index.html) from the compat report.

Run after check_skills.py:
  python3 scripts/check_skills.py --json docs/compat-report.json
  python3 scripts/build_catalog.py

The GitHub repo slug is read from $GITHUB_REPOSITORY (set automatically in
Actions) or falls back to REPO_SLUG below — update it after you create the repo.
"""

import html
import json
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPO_SLUG = os.environ.get("GITHUB_REPOSITORY", "johngraff512/mccombs-ai-skills")
REPO_URL = f"https://github.com/{REPO_SLUG}"
ZIP_URL = REPO_URL + "/releases/latest/download/{skill}.zip"

BADGES = {
    "both": ("Both platforms", "#2e7d32"),
    "both-with-caveats": ("Both (see notes)", "#b26a00"),
    "claude-only": ("Claude only", "#5f3dc4"),
}

CSS = """
body{font-family:-apple-system,Segoe UI,Helvetica,Arial,sans-serif;margin:0;background:#faf9f7;color:#333}
header{background:#BF5700;color:#fff;padding:28px 32px}
header h1{margin:0 0 4px;font-size:26px} header p{margin:0;opacity:.9}
main{max-width:960px;margin:24px auto;padding:0 16px}
input#q{width:100%;padding:10px 14px;font-size:15px;border:1px solid #ccc;border-radius:8px;margin-bottom:18px;box-sizing:border-box}
.card{background:#fff;border:1px solid #e3e0db;border-radius:10px;padding:18px 20px;margin-bottom:14px}
.card h2{margin:0 0 2px;font-size:18px} .plugin{color:#888;font-size:12px;text-transform:uppercase;letter-spacing:.04em}
.badge{display:inline-block;color:#fff;border-radius:20px;padding:2px 10px;font-size:12px;margin-left:8px;vertical-align:2px}
.desc{margin:8px 0 10px;font-size:14px;line-height:1.45}
details{font-size:13px;margin-top:6px} summary{cursor:pointer;color:#BF5700;font-weight:600}
.notes li{margin:2px 0} .install{background:#f5f2ee;border-radius:8px;padding:10px 14px;margin-top:8px}
.install b{display:block;margin-bottom:2px}
footer{max-width:960px;margin:30px auto;padding:0 16px 40px;color:#888;font-size:12px}
code{background:#f0ede8;padding:1px 5px;border-radius:4px;font-size:12px}
h2.section{font-size:15px;text-transform:uppercase;letter-spacing:.06em;color:#BF5700;border-bottom:2px solid #BF5700;padding-bottom:4px;margin:26px 0 14px}
"""

JS = """
document.getElementById('q').addEventListener('input',e=>{const v=e.target.value.toLowerCase();
document.querySelectorAll('.card').forEach(c=>{c.style.display=c.textContent.toLowerCase().includes(v)?'':'none'})});
"""


def card(r):
    label, color = BADGES[r["classification"]]
    zip_link = ZIP_URL.format(skill=r["skill"])
    notes = "".join(f"<li>{html.escape(s)}</li>" for s in r["signals"])
    notes_html = f"<details><summary>Compatibility notes</summary><ul class='notes'>{notes}</ul></details>" if notes else ""
    chatgpt = ("<div class='install'><b>ChatGPT (UT workspace)</b>"
               f"<a href='{zip_link}'>Download {r['skill']}.zip</a> &rarr; ChatGPT &rarr; Skills &rarr; Create &rarr; Upload from your computer.</div>"
               if r["classification"] != "claude-only" else
               "<div class='install'><b>ChatGPT</b> Not available — this skill depends on Claude-side features.</div>")
    ver = f" &middot; v{html.escape(str(r['version']))}" if r.get("version") else ""
    return f"""
<div class="card">
  <span class="plugin">{html.escape(r['plugin'])}{ver}</span>
  <h2>{html.escape(r['skill'])}<span class="badge" style="background:{label and color}">{label}</span></h2>
  <p class="desc">{html.escape(r['description'])}</p>
  <div class="install"><b>Claude (UT Claude EDU)</b>
    <a href="{zip_link}">Download {r['skill']}.zip</a> &rarr; Claude &rarr; Settings &rarr; Capabilities &rarr; Skills &rarr; Upload skill.</div>
  {chatgpt}
  {notes_html}
</div>"""


def plugin_cards(report):
    """One card per plugin: whole-toolkit zip + marketplace command."""
    manifest = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    by_plugin = {}
    for r in report:
        by_plugin.setdefault(r["plugin"], []).append(r["skill"])
    out = []
    for p in manifest["plugins"]:
        skills = by_plugin.get(p["name"])
        if not skills:
            continue
        zip_link = ZIP_URL.format(skill=f"{p['name']}-plugin")
        out.append(f"""
<div class="card">
  <span class="plugin">Toolkit &middot; {len(skills)} skills</span>
  <h2>{html.escape(p['name'])}</h2>
  <p class="desc">{html.escape(p['description'])}<br><small>Includes: {html.escape(', '.join(sorted(skills)))}</small></p>
  <div class="install"><b>Claude Code / Cowork (installs and auto-updates — no download needed)</b>
    Type: <code>/plugin marketplace add {REPO_SLUG}</code> then <code>/plugin install {html.escape(p['name'])}</code>.
    This pulls straight from GitHub and picks up future updates automatically.</div>
  <div class="install"><b>Everything as one download</b>
    <a href="{zip_link}">Download {p['name']}-plugin.zip</a> — contains all {len(skills)} skill folders.
    Note: Claude and ChatGPT skill upload work one skill at a time, so unzip it and upload the
    skills you want individually (or use the per-skill downloads below).</div>
</div>""")
    return "\n".join(out)


def main():
    report = json.loads((ROOT / "docs" / "compat-report.json").read_text())
    cards = "\n".join(card(r) for r in report)
    toolkits = plugin_cards(report)
    n = len(report)
    both = sum(1 for r in report if r["classification"] != "claude-only")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>McCombs AI Skills Catalog</title><style>{CSS}</style></head><body>
<header><h1>McCombs AI Skills Catalog</h1>
<p>{n} skills for teaching and learning &middot; {both} work in both Claude EDU and ChatGPT &middot; updated {date.today().isoformat()}</p></header>
<main><input id="q" placeholder="Search skills (e.g. case, slides, teaching note)&hellip;">
<h2 class="section">Toolkits — install a whole set at once</h2>
{toolkits}
<h2 class="section">Individual skills</h2>
{cards}</main>
<footer>Maintained by the McCombs AI Faculty Working Group &middot; <a href="{REPO_URL}">Contribute a skill on GitHub</a>
&middot; Skills follow the <a href="https://agentskills.io/specification">Agent Skills open standard</a>.</footer>
<script>{JS}</script></body></html>"""
    out = ROOT / "docs" / "index.html"
    out.write_text(page)
    print(f"Wrote {out.relative_to(ROOT)} ({n} skills)")


if __name__ == "__main__":
    main()
