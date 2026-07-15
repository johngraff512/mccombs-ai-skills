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
import re
import subprocess
from datetime import date
from pathlib import Path

try:
    import markdown  # pip install markdown (CI installs it; falls back to <pre> if missing)
except ImportError:
    markdown = None


def last_updated(path: Path) -> str:
    """Date of the last git commit touching this path (needs full clone: fetch-depth 0 in CI)."""
    try:
        out = subprocess.run(
            ["git", "log", "-1", "--format=%cs", "--", str(path)],
            capture_output=True, text=True, cwd=path.parent, timeout=10).stdout.strip()
        return out or date.today().isoformat()
    except Exception:
        return date.today().isoformat()

ROOT = Path(__file__).resolve().parent.parent
REPO_SLUG = os.environ.get("GITHUB_REPOSITORY", "johngraff512/mccombs-ai-skills")
REPO_URL = f"https://github.com/{REPO_SLUG}"
ZIP_URL = REPO_URL + "/releases/latest/download/{skill}.zip"

BADGES = {
    "both": ("Both platforms", "#2e7d32"),
    "both-with-caveats": ("Both (see notes)", "#b26a00"),
    "claude-code-only": ("Claude Code only", "#8b1a1a"),
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
.chips{margin-bottom:16px}
.chip{border:1px solid #BF5700;background:#fff;color:#BF5700;border-radius:20px;padding:5px 14px;margin:0 6px 6px 0;font-size:13px;cursor:pointer}
.chip.on{background:#BF5700;color:#fff}
.cat{display:inline-block;background:#f0ede8;color:#665;border-radius:20px;padding:2px 10px;font-size:12px;margin-left:6px;vertical-align:2px}
a.more{color:#BF5700;font-weight:600;text-decoration:none;white-space:nowrap}
.contribute{float:right;font-size:14px}.contribute a{color:#fff;text-decoration:underline}
"""

JS = """
let activeCat = null;
function applyFilters(){
  const v = document.getElementById('q').value.toLowerCase();
  document.querySelectorAll('.card').forEach(c => {
    const okText = c.textContent.toLowerCase().includes(v);
    const okCat = !activeCat || !c.dataset.category || c.dataset.category === activeCat;
    c.style.display = (okText && okCat) ? '' : 'none';
  });
}
document.getElementById('q').addEventListener('input', applyFilters);
document.querySelectorAll('.chip').forEach(b => b.addEventListener('click', () => {
  activeCat = (activeCat === b.dataset.cat) ? null : b.dataset.cat;
  document.querySelectorAll('.chip').forEach(x => x.classList.toggle('on', x.dataset.cat === activeCat));
  applyFilters();
}));
"""


def card(r):
    label, color = BADGES[r["classification"]]
    zip_link = ZIP_URL.format(skill=r["skill"])
    notes = "".join(f"<li>{html.escape(s)}</li>" for s in r["signals"])
    notes_html = f"<details><summary>Compatibility notes</summary><ul class='notes'>{notes}</ul></details>" if notes else ""
    cls = r["classification"]
    if cls == "claude-code-only":
        claude = ("<div class='install'><b>Claude Code (developer tool)</b> This skill needs software on your own computer, "
                  f"so it only works in Claude Code: <code>/plugin marketplace add {REPO_SLUG}</code></div>")
        chatgpt = "<div class='install'><b>Claude (web/desktop) and ChatGPT</b> Not available — see the notes below.</div>"
    elif cls == "claude-only":
        claude = (f"<div class='install'><b>Claude (UT Claude EDU)</b> <a href='{zip_link}'>Download {r['skill']}.zip</a> "
                  "&rarr; Claude &rarr; Settings &rarr; Capabilities &rarr; Skills &rarr; Upload skill.</div>")
        chatgpt = "<div class='install'><b>ChatGPT</b> Not available — this skill depends on Claude-only features (see notes).</div>"
    else:
        claude = (f"<div class='install'><b>Claude (UT Claude EDU)</b> <a href='{zip_link}'>Download {r['skill']}.zip</a> "
                  "&rarr; Claude &rarr; Settings &rarr; Capabilities &rarr; Skills &rarr; Upload skill.</div>")
        chatgpt = (f"<div class='install'><b>ChatGPT (UT workspace)</b> <a href='{zip_link}'>Download {r['skill']}.zip</a> "
                   "&rarr; ChatGPT &rarr; Skills &rarr; Create &rarr; Upload from your computer.</div>")
    ver = f" &middot; v{html.escape(str(r['version']))}" if r.get("version") else ""
    cat = r.get("category", "General")
    updated = last_updated(ROOT / "plugins" / r["plugin"] / "skills" / r["skill"])
    detail_page(r, label, color)
    return f"""
<div class="card" data-category="{html.escape(cat)}">
  <span class="plugin">{html.escape(r['plugin'])}{ver} &middot; updated {updated}</span>
  <h2>{html.escape(r['skill'])}<span class="badge" style="background:{label and color}">{label}</span><span class="cat">{html.escape(cat)}</span></h2>
  <p class="desc">{html.escape(r['description'])}
  <a class="more" href="skills/{r['skill']}.html">Learn more &rarr;</a></p>
  {claude}
  {chatgpt}
  {notes_html}
</div>"""


def render_md(src: str) -> str:
    if markdown:
        return markdown.markdown(src, extensions=["tables", "fenced_code"])
    return f"<pre style='white-space:pre-wrap'>{html.escape(src)}</pre>"


def detail_page(r, badge_label, badge_color):
    """Write docs/skills/<skill>.html — full documentation so faculty can read before installing."""
    skill_dir = ROOT / "plugins" / r["plugin"] / "skills" / r["skill"]
    readme = skill_dir / "README.md"
    if readme.exists():
        src, source_note = readme.read_text(encoding="utf-8", errors="replace"), "the skill's README"
    else:
        raw = (skill_dir / "SKILL.md").read_text(encoding="utf-8", errors="replace")
        src = re.sub(r"^---\n.*?\n---\n", "", raw, flags=re.S)
        source_note = "the skill's full instructions (SKILL.md) — exactly what the AI follows when you use it"
    files = sorted(str(p.relative_to(skill_dir)) for p in skill_dir.rglob("*") if p.is_file())
    file_list = "".join(f"<li><code>{html.escape(f)}</code></li>" for f in files)
    zip_link = ZIP_URL.format(skill=r["skill"])
    notes = "".join(f"<li>{html.escape(s)}</li>" for s in r["signals"])
    notes_html = f"<h3>Compatibility notes</h3><ul>{notes}</ul>" if notes else ""
    ver = f"v{html.escape(str(r['version']))} &middot; " if r.get("version") else ""
    if r["classification"] == "claude-code-only":
        install = ("<div class='install'><b>Install (Claude Code only)</b> This skill runs software on your own computer, "
                   f"so it works only in Claude Code: <code>/plugin marketplace add {REPO_SLUG}</code></div>")
    elif r["classification"] == "claude-only":
        install = (f"<div class='install'><b>Install (Claude only)</b> <a href='{zip_link}'>Download {r['skill']}.zip</a> "
                   "&mdash; upload in Claude: Settings &rarr; Capabilities &rarr; Skills &rarr; Upload skill. Not available for ChatGPT.</div>")
    else:
        install = (f"<div class='install'><b>Install</b> <a href='{zip_link}'>Download {r['skill']}.zip</a> &mdash; then upload in "
                   "<b>Claude</b> (Settings &rarr; Capabilities &rarr; Skills &rarr; Upload skill) or "
                   "<b>ChatGPT</b> (Skills &rarr; Create &rarr; Upload from your computer).</div>")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(r['skill'])} — McCombs AI Skills</title><style>{CSS}
.doc{{background:#fff;border:1px solid #e3e0db;border-radius:10px;padding:20px 24px;line-height:1.55;font-size:14px}}
.doc h1,.doc h2,.doc h3{{color:#333}} .doc pre{{background:#f5f2ee;padding:10px;border-radius:6px;overflow-x:auto}}
a.back{{color:#BF5700;font-weight:600;text-decoration:none}}</style></head><body>
<header><h1>{html.escape(r['skill'])}</h1>
<p>{html.escape(r['plugin'])} &middot; {ver}{html.escape(r.get('category', 'General'))} &middot;
<span class="badge" style="background:{badge_color}">{badge_label}</span></p></header>
<main><p><a class="back" href="../index.html">&larr; Back to catalog</a></p>
{install}
{notes_html}
<h3>About this skill</h3>
<p><small>The content below is {source_note}.</small></p>
<div class="doc">{render_md(src)}</div>
<h3>Files included</h3><ul>{file_list}</ul>
<p><a class="back" href="../index.html">&larr; Back to catalog</a></p></main>
<footer>McCombs AI Skills &middot; <a href="{REPO_URL}/blob/master/CONTRIBUTING.md">How to contribute or update a skill</a></footer>
</body></html>"""
    out = ROOT / "docs" / "skills" / f"{r['skill']}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)


def toolkit_detail_page(name, pj, skills):
    """Write docs/toolkits/<name>.html rendering the toolkit's README."""
    readme = ROOT / "toolkits" / name / "README.md"
    src = readme.read_text(encoding="utf-8", errors="replace") if readme.exists() else pj.get("description", "")
    ver = pj.get("version", "?")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(name)} — McCombs AI Skills</title><style>{CSS}
.doc{{background:#fff;border:1px solid #e3e0db;border-radius:10px;padding:20px 24px;line-height:1.55;font-size:14px}}
.doc pre{{background:#f5f2ee;padding:10px;border-radius:6px;overflow-x:auto}}
.doc table{{border-collapse:collapse}} .doc td,.doc th{{border:1px solid #e3e0db;padding:4px 10px;font-size:13px}}
a.back{{color:#BF5700;font-weight:600;text-decoration:none}}</style></head><body>
<header><h1>{html.escape(name)}</h1><p>Plug-in &middot; v{html.escape(ver)} &middot; {len(skills)} skills</p></header>
<main><p><a class="back" href="../index.html">&larr; Back to catalog</a></p>
<div class="doc">{render_md(src)}</div>
<p><a class="back" href="../index.html">&larr; Back to catalog</a></p></main>
<footer>McCombs AI Skills &middot; <a href="{REPO_URL}">GitHub repository</a></footer>
</body></html>"""
    out = ROOT / "docs" / "toolkits" / f"{name}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)


def plugin_cards(report):
    """One card per curated toolkit. A plugin qualifies only if it has a source tree
    under toolkits/<name>/ — plain groupings (community-skills, business-ai-tools)
    appear as individual skills only, to avoid presenting them as products."""
    manifest = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    by_plugin = {}
    for r in report:
        by_plugin.setdefault(r["plugin"], []).append(r["skill"])
    out = []
    for p in manifest["plugins"]:
        skills = by_plugin.get(p["name"])
        if not skills or not (ROOT / "toolkits" / p["name"]).is_dir():
            continue
        pj = json.loads((ROOT / "plugins" / p["name"] / ".claude-plugin" / "plugin.json").read_text())
        ver = pj.get("version", "?")
        updated = last_updated(ROOT / "plugins" / p["name"])
        claude_zip = ZIP_URL.format(skill=f"{p['name']}-v{ver}")
        chatgpt_zip = ZIP_URL.format(skill=f"{p['name']}-chatgpt-v{ver}")
        toolkit_detail_page(p["name"], pj, skills)
        out.append(f"""
<div class="card">
  <span class="plugin">Plug-in (for Claude only) &middot; {len(skills)} skills &middot; v{html.escape(ver)} &middot; updated {updated}</span>
  <h2>{html.escape(p['name'])}</h2>
  <p class="desc">{html.escape(p['description'])}<br><small>Includes: {html.escape(', '.join(sorted(skills)))}</small>
  <a class="more" href="toolkits/{p['name']}.html">Learn more &rarr;</a></p>
  <div class="install"><b>Claude plug-in (Claude Code / Cowork only — installs and auto-updates, no download)</b>
    Type: <code>/plugin marketplace add {REPO_SLUG}</code> then <code>/plugin install {html.escape(p['name'])}</code>.
    ChatGPT and the Claude website don't support plug-ins — use the downloads below instead.</div>
  <div class="install"><b>Claude website / desktop app (upload once)</b>
    <a href="{claude_zip}">Download {p['name']}-v{ver}.zip</a> — unzip and upload the
    skills you want in Claude: Settings &rarr; Capabilities &rarr; Skills &rarr; Upload skill.</div>
  <div class="install"><b>ChatGPT (upload once)</b>
    <a href="{chatgpt_zip}">Download {p['name']}-chatgpt-v{ver}.zip</a> — unzip it, then upload each enclosed
    skill.zip in ChatGPT: Skills &rarr; Create &rarr; Upload from your computer.</div>
</div>""")
    return "\n".join(out)


def main():
    report = json.loads((ROOT / "docs" / "compat-report.json").read_text())
    cards = "\n".join(card(r) for r in report)
    toolkits = plugin_cards(report)
    toolkit_section = f'<h2 class="section">Plug-ins — install a whole skill set at once</h2>\n{toolkits}' if toolkits else ""
    cats = sorted({r.get("category", "General") for r in report})
    chips = "".join(f'<button class="chip" data-cat="{html.escape(c)}">{html.escape(c)}</button>' for c in cats)
    n = len(report)
    both = sum(1 for r in report if r["classification"] != "claude-only")
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>McCombs AI Skills Catalog</title><style>{CSS}</style></head><body>
<header><span class="contribute"><a href="{REPO_URL}/blob/master/CONTRIBUTING.md">Contribute a skill (no coding needed)</a></span>
<h1>McCombs AI Skills Catalog</h1>
<p>{n} skills for teaching and learning &middot; {both} work in both Claude EDU and ChatGPT &middot; updated {date.today().isoformat()}</p></header>
<main><input id="q" placeholder="Search skills (e.g. case, slides, teaching note)&hellip;">
<div class="chips">{chips}</div>
{toolkit_section}
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
