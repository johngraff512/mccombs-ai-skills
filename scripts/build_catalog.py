#!/usr/bin/env python3
"""Build the faculty-facing skill catalog (docs/index.html) from the compat report.

Run after check_skills.py:
  python3 scripts/check_skills.py --json docs/compat-report.json
  python3 scripts/build_catalog.py

Requires the `markdown` package for detail pages (CI installs it; a local run
without it falls back to <pre> rendering and degrades every page — install it).

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

# classification -> (faculty-facing badge label, badge tone class)
BADGES = {
    "both": ("Claude &amp; ChatGPT", "ok"),
    "both-with-caveats": ("Claude &amp; ChatGPT &middot; notes", "warn"),
    "claude-code-only": ("Needs local software", "flag"),
    "claude-only": ("Claude only", "claude"),
}

# Preferred category order for the homepage sections (unknown categories sort after, alphabetically).
CATEGORY_ORDER = ["Case Writing", "Class Preparation", "Slides & Presentations",
                  "Research & Summaries", "Decision Support", "General"]

CSS = """
:root{
  --bg:#FAF7F2; --surface:#FFFFFF; --ink:#2B241D; --muted:#75695C; --line:#E8E0D4;
  --accent:#BF5700; --accent-deep:#993F00; --accent-soft:#F7E8DC;
  --ok:#3B7A3F; --warn:#A96A00; --flag:#96261B; --claude:#40598C;
  --shadow:0 1px 3px rgba(43,36,29,.07);
}
@media (prefers-color-scheme: dark){:root{
  --bg:#211B15; --surface:#2B241D; --ink:#F0E9DF; --muted:#AB9E8E; --line:#3D352B;
  --accent:#F28C3B; --accent-deep:#F8A867; --accent-soft:#3B2A1C;
  --ok:#7CBB80; --warn:#E0A44C; --flag:#E58074; --claude:#93A9DB;
  --shadow:0 1px 3px rgba(0,0,0,.35);
}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 -apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
h1,h2,h3{font-family:Charter,"Iowan Old Style",Georgia,serif;text-wrap:balance}
a{color:var(--accent-deep)}
code,.mono{font-family:ui-monospace,"SF Mono",Menlo,monospace;font-size:.86em}
code{background:var(--accent-soft);padding:1px 6px;border-radius:4px}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header.site{background:#BF5700;color:#fff;padding:26px 0 22px}
header.site h1{margin:0;font-size:26px;font-weight:600}
header.site p{margin:4px 0 0;opacity:.92;font-size:14px}
header.site a{color:#fff}
/* toolbar */
.toolbar{position:sticky;top:0;z-index:5;background:var(--bg);border-bottom:1px solid var(--line);padding:14px 0 10px}
.toolrow{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
input#q{flex:1 1 260px;padding:9px 14px;font-size:15px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink)}
input#q:focus{outline:2px solid var(--accent);outline-offset:1px}
select{padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--ink);font-size:13.5px}
.count{font-size:13px;color:var(--muted);white-space:nowrap;font-variant-numeric:tabular-nums}
.chips{display:flex;gap:6px;flex-wrap:wrap;margin-top:10px}
.chip{border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:18px;
  padding:4px 12px;font-size:13px;cursor:pointer}
.chip .n{color:var(--muted);font-variant-numeric:tabular-nums;margin-left:4px}
.chip.on{background:var(--accent);border-color:var(--accent);color:#fff}
.chip.on .n{color:#fff;opacity:.85}
.chip:focus-visible,.card:focus-visible,button:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
/* toolkit band */
.band{display:flex;gap:18px;align-items:center;background:linear-gradient(100deg,var(--accent-soft),var(--surface) 70%);
  border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin:18px 0 6px;flex-wrap:wrap}
.band h2{margin:0 0 3px;font-size:19px}
.band p{margin:0;font-size:13.5px;color:var(--muted);max-width:62ch}
.band .cta{margin-left:auto}
.btn{display:inline-block;background:var(--accent);color:#fff;border:none;border-radius:8px;
  padding:9px 16px;font-size:14px;font-weight:600;cursor:pointer;text-decoration:none}
/* grid */
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:12px;margin:16px 0 40px}
.gsec{grid-column:1/-1;font-size:13px;text-transform:uppercase;letter-spacing:.07em;color:var(--accent-deep);
  border-bottom:2px solid var(--accent);padding:14px 0 4px;margin:0;font-family:inherit;font-weight:700}
.card{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 16px;
  box-shadow:var(--shadow);display:flex;flex-direction:column;gap:6px;position:relative}
.card:hover{border-color:var(--accent)}
.card h3{margin:0;font-size:16.5px;font-weight:600;font-family:inherit}
.card h3 a{color:inherit;text-decoration:none}
.card h3 a::after{content:"";position:absolute;inset:0}
.card .sum{margin:0;font-size:13.5px;color:var(--muted);line-height:1.45;flex:1}
.meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;font-size:12px;color:var(--muted)}
.badge{font-size:11.5px;font-weight:600;border-radius:5px;padding:1.5px 7px;white-space:nowrap;
  color:var(--tone);background:color-mix(in srgb,var(--tone) 12%,transparent)}
.badge.ok{--tone:var(--ok)}.badge.warn{--tone:var(--warn)}.badge.flag{--tone:var(--flag)}.badge.claude{--tone:var(--claude)}
.plats{display:flex;gap:10px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:8px;margin-top:2px}
.plats .no{opacity:.45;text-decoration:line-through}
.empty{grid-column:1/-1;text-align:center;color:var(--muted);padding:50px 0;display:none}
/* detail pages */
.detail{max-width:760px;margin:26px auto 60px}
a.back{display:inline-block;margin-bottom:14px;font-size:14px;text-decoration:none;font-weight:600;color:var(--accent-deep)}
.dhead{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:22px 24px;box-shadow:var(--shadow)}
.dhead h2{margin:0 0 4px;font-size:26px}
.dhead .sum{font-size:15.5px;margin:10px 0 0;max-width:65ch}
.install{margin:20px 0}
.acc{background:var(--surface);border:1px solid var(--line);border-radius:10px;margin-bottom:8px;overflow:hidden}
.acc summary{cursor:pointer;padding:12px 16px;font-weight:600;font-size:14.5px;display:flex;gap:10px;align-items:center}
.acc summary .tag{margin-left:auto;font-weight:400;font-size:12.5px;color:var(--muted);text-align:right}
.acc .body{padding:0 16px 14px;font-size:14px}
.acc ol{margin:6px 0;padding-left:22px}.acc li{margin:4px 0}
.acc.unavail .head{display:flex;gap:10px;align-items:center;padding:12px 16px;font-weight:600;font-size:14.5px;color:var(--muted)}
.panel{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:14px 18px;margin:14px 0}
.panel h3,.install h3{margin:0 0 8px;font-size:15px;font-family:inherit}
.panel ul{margin:0;padding-left:20px;font-size:13.5px;color:var(--muted)}
.doc{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:20px 24px;line-height:1.55;font-size:14px}
.doc pre{background:var(--bg);padding:10px;border-radius:6px;overflow-x:auto}
.doc table{border-collapse:collapse;display:block;overflow-x:auto}
.doc td,.doc th{border:1px solid var(--line);padding:4px 10px;font-size:13px}
footer{color:var(--muted);font-size:12.5px;padding:18px 0 44px;border-top:1px solid var(--line)}
footer a{color:var(--accent-deep)}
@media (max-width:640px){.band .cta{margin-left:0}.detail{margin-top:16px}}
"""

JS = """
const grid=document.getElementById('grid');
const cards=[...grid.querySelectorAll('.card')];
const heads=[...grid.querySelectorAll('.gsec')];
const original=[...grid.children];
const q=document.getElementById('q'), sort=document.getElementById('sort');
const count=document.getElementById('count'), empty=document.getElementById('empty');
let activeCat=null;
function apply(){
  const v=q.value.toLowerCase();
  let shown=0;
  cards.forEach(c=>{
    const ok=(!activeCat||c.dataset.category===activeCat)&&c.textContent.toLowerCase().includes(v);
    c.style.display=ok?'':'none'; c.dataset.on=ok?'1':''; if(ok)shown++;
  });
  if(sort.value==='cat'){
    original.forEach(el=>grid.appendChild(el));
    heads.forEach(h=>{h.style.display=cards.some(c=>c.dataset.on&&c.dataset.category===h.dataset.cat)?'':'none'});
  }else{
    heads.forEach(h=>h.style.display='none');
    const key=sort.value==='az'
      ?(a,b)=>a.dataset.name.localeCompare(b.dataset.name)
      :(a,b)=>b.dataset.updated.localeCompare(a.dataset.updated)||a.dataset.name.localeCompare(b.dataset.name);
    [...cards].sort(key).forEach(c=>grid.appendChild(c));
    grid.appendChild(empty);
  }
  count.textContent=`${shown} of ${cards.length}`;
  empty.style.display=shown?'none':'block';
}
q.addEventListener('input',apply);
sort.addEventListener('change',apply);
document.querySelectorAll('.chip').forEach(b=>b.addEventListener('click',()=>{
  activeCat=(activeCat===b.dataset.cat)?null:b.dataset.cat;
  document.querySelectorAll('.chip').forEach(x=>x.classList.toggle('on',x.dataset.cat===activeCat));
  apply();
}));
"""


def summary_of(r) -> str:
    """metadata.summary, or the description truncated at a sentence/word boundary."""
    if r.get("summary"):
        return r["summary"]
    desc = r.get("description", "")
    first = re.split(r"(?<=[.!?])\s", desc, 1)[0]
    if len(first) <= 160:
        return first
    return first[:157].rsplit(" ", 1)[0] + "…"


def platform_marks(cls: str) -> str:
    gpt_ok = cls in ("both", "both-with-caveats")
    marks = ["<span>Claude ✓</span>",
             f"<span class=\"{'' if gpt_ok else 'no'}\">ChatGPT{' ✓' if gpt_ok else ''}</span>"]
    if cls == "claude-code-only":
        marks.append('<span title="Runs software that must be installed locally">⚙ local software</span>')
    return f"<div class='plats'>{''.join(marks)}</div>"


def badge(cls: str) -> str:
    label, tone = BADGES[cls]
    return f"<span class='badge {tone}'>{label}</span>"


def page_shell(title: str, body: str, header: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — McCombs AI Skills</title><style>{CSS}</style></head><body>
<header class="site"><div class="wrap">{header}</div></header>
{body}
</body></html>"""


def card(r):
    cls = r["classification"]
    cat = r.get("category", "General")
    updated = last_updated(ROOT / "plugins" / r["plugin"] / "skills" / r["skill"])
    detail_page(r, updated)
    ver = f"<span>v{html.escape(str(r['version']))}</span>" if r.get("version") else ""
    return f"""
<div class="card" data-category="{html.escape(cat)}" data-name="{html.escape(r['skill'])}" data-updated="{updated}">
  <h3><a href="skills/{r['skill']}.html">{html.escape(r['skill'])}</a></h3>
  <p class="sum">{html.escape(summary_of(r))}</p>
  <div class="meta">{badge(cls)}{ver}<span>&middot;</span><span>{html.escape(r['plugin'])}</span></div>
  {platform_marks(cls)}
</div>"""


def render_md(src: str) -> str:
    if markdown:
        return markdown.markdown(src, extensions=["tables", "fenced_code"])
    return f"<pre style='white-space:pre-wrap'>{html.escape(src)}</pre>"


def install_accordions(r) -> str:
    """Per-platform install steps as expandable accordions (Option A detail layout)."""
    cls = r["classification"]
    zip_link = ZIP_URL.format(skill=r["skill"])
    name = html.escape(r["skill"])
    if cls == "claude-code-only":
        claude_tag, claude_body = "Claude Code recommended", (
            f"<p>This skill runs extra software (see notes below) that hosted platforms don't preinstall. "
            f"Recommended: <b>Claude Code</b> on a computer with that software:</p>"
            f"<ol><li>Run <code>/plugin marketplace add {REPO_SLUG}</code>, or</li>"
            f"<li><a href='{zip_link}'>Download {name}.zip</a> and unzip into <code>~/.claude/skills/</code>.</li></ol>"
            f"<p>It may also work in <b>Claude Cowork</b> if the software can be installed in its environment. "
            f"Uploading the zip to claude.ai's hosted Skills won't work — the required software isn't available there.</p>")
    else:
        claude_tag, claude_body = "~1 minute", (
            f"<ol><li><a href='{zip_link}'>Download {name}.zip</a></li>"
            f"<li>In Claude: <b>Settings → Capabilities → Skills → Upload skill</b>.</li></ol>")
    out = (f"<details class='acc' open><summary>🟠 Claude (UT Claude EDU)"
           f"<span class='tag'>{claude_tag}</span></summary><div class='body'>{claude_body}</div></details>")
    if cls in ("both", "both-with-caveats"):
        out += (f"<details class='acc'><summary>🟢 ChatGPT (UT workspace)<span class='tag'>~1 minute</span></summary>"
                f"<div class='body'><ol><li><a href='{zip_link}'>Download {name}.zip</a></li>"
                f"<li>In ChatGPT: <b>Skills → Create → Upload from your computer</b>.</li></ol></div></details>")
    else:
        reason = ("can't install the required software" if cls == "claude-code-only"
                  else "uses Claude-only features (see notes)")
        out += (f"<div class='acc unavail'><div class='head'>⚪ ChatGPT"
                f"<span class='tag'>Not available — {reason}</span></div></div>")
    return out


def detail_page(r, updated):
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
    notes = "".join(f"<li>{html.escape(s)}</li>" for s in r["signals"])
    notes_html = f"<div class='panel'><h3>Good to know</h3><ul>{notes}</ul></div>" if notes else ""
    ver = f"<span class='mono'>v{html.escape(str(r['version']))}</span><span>&middot;</span>" if r.get("version") else ""
    header = f"<h1>McCombs AI Skills</h1><p>Ready-to-use AI skills for teaching and learning</p>"
    body = f"""<main class="wrap detail">
<a class="back" href="../index.html">← All skills</a>
<div class="dhead"><div class="meta" style="margin-bottom:6px">{badge(r['classification'])}
  <span>{html.escape(r.get('category', 'General'))}</span><span>&middot;</span>
  <span>{html.escape(r['plugin'])}</span><span>&middot;</span>
  {ver}<span>updated {updated}</span></div>
  <h2>{html.escape(r['skill'])}</h2><p class="sum">{html.escape(summary_of(r))}</p></div>
<div class="install"><h3>Install</h3>{install_accordions(r)}</div>
{notes_html}
<div class="panel"><h3>About this skill</h3>
<p style="font-size:12.5px;color:var(--muted);margin:0 0 10px">The content below is {source_note}.</p>
<div class="doc">{render_md(src)}</div></div>
<details class="acc"><summary>Files included<span class="tag">{len(files)}</span></summary>
<div class="body"><ul>{file_list}</ul></div></details>
<a class="back" href="../index.html">← All skills</a>
<footer style="border:none;padding-top:8px">McCombs AI Skills &middot; <a href="{REPO_URL}/blob/master/CONTRIBUTING.md">How to contribute or update a skill</a></footer>
</main>"""
    out = ROOT / "docs" / "skills" / f"{r['skill']}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page_shell(r["skill"], body, header))


def toolkit_detail_page(name, pj, skills):
    """Write docs/toolkits/<name>.html — install options plus the toolkit's README."""
    readme = ROOT / "toolkits" / name / "README.md"
    src = readme.read_text(encoding="utf-8", errors="replace") if readme.exists() else pj.get("description", "")
    ver = pj.get("version", "?")
    claude_zip = ZIP_URL.format(skill=f"{name}-v{ver}")
    chatgpt_zip = ZIP_URL.format(skill=f"{name}-chatgpt-v{ver}")
    header = f"<h1>McCombs AI Skills</h1><p>Ready-to-use AI skills for teaching and learning</p>"
    body = f"""<main class="wrap detail">
<a class="back" href="../index.html">← All skills</a>
<div class="dhead"><div class="meta" style="margin-bottom:6px"><span class='badge ok'>Plug-in</span>
  <span>{len(skills)} skills</span><span>&middot;</span><span class="mono">v{html.escape(ver)}</span></div>
  <h2>{html.escape(name)}</h2><p class="sum">{html.escape(pj.get('description', ''))}</p></div>
<div class="install"><h3>Install</h3>
<details class="acc" open><summary>🟠 Claude plug-in<span class="tag">recommended — one install, auto-updates</span></summary>
<div class="body"><p>Works on the Claude website, desktop app, Cowork, and Claude Code.</p>
<ol><li>On the website/app: <b>Customize → Plugins → + → Add marketplace</b> → enter <code>{REPO_SLUG}</code>, then install <b>{html.escape(name)}</b>.</li>
<li>In Claude Code: <code>/plugin marketplace add {REPO_SLUG}</code>.</li></ol>
<p>ChatGPT doesn't support plug-ins — see below.</p></div></details>
<details class="acc"><summary>🟠 Claude manual upload<span class="tag">upload once, no auto-updates</span></summary>
<div class="body"><ol><li><a href="{claude_zip}">Download {html.escape(name)}-v{html.escape(ver)}.zip</a></li>
<li>Unzip, then upload the skills you want in Claude: <b>Settings → Capabilities → Skills → Upload skill</b>.</li></ol></div></details>
<details class="acc"><summary>🟢 ChatGPT (UT workspace)<span class="tag">upload once</span></summary>
<div class="body"><ol><li><a href="{chatgpt_zip}">Download {html.escape(name)}-chatgpt-v{html.escape(ver)}.zip</a></li>
<li>Unzip it, then upload each enclosed skill.zip in ChatGPT: <b>Skills → Create → Upload from your computer</b>.</li></ol></div></details>
</div>
<div class="panel"><h3>About this plug-in</h3><div class="doc">{render_md(src)}</div></div>
<a class="back" href="../index.html">← All skills</a>
<footer style="border:none;padding-top:8px">McCombs AI Skills &middot; <a href="{REPO_URL}">GitHub repository</a></footer>
</main>"""
    out = ROOT / "docs" / "toolkits" / f"{name}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page_shell(name, body, header))


def toolkit_bands(report):
    """One promoted band per curated toolkit. A plugin qualifies only if it has a source tree
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
        toolkit_detail_page(p["name"], pj, skills)
        out.append(f"""
<div class="band"><div><h2>📦 {html.escape(p['name'])} <span class="mono" style="font-size:12px;color:var(--muted)">v{html.escape(ver)}</span></h2>
  <p>{html.escape(p['description'])} <b>{len(skills)} skills, one install, auto-updates in Claude.</b></p></div>
  <span class="cta"><a class="btn" href="toolkits/{p['name']}.html">Install the plug-in →</a></span></div>""")
    return "\n".join(out)


def main():
    report = json.loads((ROOT / "docs" / "compat-report.json").read_text())
    bands = toolkit_bands(report)
    cats = sorted({r.get("category", "General") for r in report},
                  key=lambda c: (CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else len(CATEGORY_ORDER), c))
    by_cat = {c: sorted((r for r in report if r.get("category", "General") == c),
                        key=lambda r: r["skill"]) for c in cats}
    chips = "".join(
        f'<button class="chip" data-cat="{html.escape(c)}">{html.escape(c)}<span class="n">{len(by_cat[c])}</span></button>'
        for c in cats)
    grid = ""
    for c in cats:
        grid += f'<h2 class="gsec" data-cat="{html.escape(c)}">{html.escape(c)} &middot; {len(by_cat[c])}</h2>'
        grid += "".join(card(r) for r in by_cat[c])
    n = len(report)
    both = sum(1 for r in report if r["classification"] in ("both", "both-with-caveats"))
    header = f"""<span style="float:right;font-size:14px"><a href="{REPO_URL}/blob/master/CONTRIBUTING.md">Contribute a skill (no coding needed)</a></span>
<h1>McCombs AI Skills</h1>
<p>{n} ready-to-use AI skills for teaching and learning &middot; {both} work in both Claude EDU and ChatGPT &middot; updated {date.today().isoformat()}</p>"""
    body = f"""<div class="toolbar"><div class="wrap">
<div class="toolrow">
  <input id="q" type="search" placeholder="Search {n} skills — try “case”, “slides”, “teaching note”…">
  <select id="sort" aria-label="Sort">
    <option value="cat" selected>By category</option>
    <option value="az">A–Z</option>
    <option value="new">Recently updated</option></select>
  <span class="count" id="count">{n} of {n}</span></div>
<div class="chips">{chips}</div>
</div></div>
<main class="wrap">
{bands}
<div class="grid" id="grid">{grid}<div class="empty" id="empty">No skills match — try a broader term.</div></div>
<footer>Maintained by the McCombs AI Faculty Working Group &middot; <a href="{REPO_URL}">Contribute a skill on GitHub</a>
&middot; Skills follow the <a href="https://agentskills.io/specification">Agent Skills open standard</a>.</footer>
</main>
<script>{JS}</script>"""
    out = ROOT / "docs" / "index.html"
    out.write_text(page_shell("Catalog", body, header))
    print(f"Wrote {out.relative_to(ROOT)} ({n} skills)")
    if markdown is None:
        print("WARNING: python 'markdown' package not installed — detail pages degraded to <pre> rendering.")


if __name__ == "__main__":
    main()
