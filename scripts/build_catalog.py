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

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

try:
    import markdown  # pip install markdown (CI installs it; falls back to <pre> if missing)
except ImportError:
    markdown = None

ROOT = Path(__file__).resolve().parent.parent
REPO_SLUG = os.environ.get("GITHUB_REPOSITORY", "johngraff512/mccombs-ai-skills")
REPO_URL = f"https://github.com/{REPO_SLUG}"
ZIP_URL = REPO_URL + "/releases/latest/download/{skill}.zip"

# last_updated() bookkeeping.
_DATE_CACHE = {}     # path -> resolved date; each path is asked for twice (card + detail page)
_TRACKED = None      # set of files in the git index (None = not read yet)
DATE_ERRORS = []     # git failed — any date we print is a guess
DATE_UNTRACKED = []  # no commits yet — today's date is genuinely right
_GIT_TIMEOUT = 30    # generous: a cold object store can make even small reads slow


def _rel(path: Path) -> str:
    """Path relative to the repo root, slash-separated, as git reports it."""
    try:
        return str(path.relative_to(ROOT)).replace(os.sep, "/")
    except ValueError:
        return str(path)


def _git(args, what):
    """Run a git command from ROOT. Returns stdout, or None if git failed.

    A failure is recorded in DATE_ERRORS rather than swallowed, because the
    caller's only fallback is today's date — a guess that would otherwise be
    published to the live site with nothing to signal it.
    """
    try:
        proc = subprocess.run(["git", "-c", "core.quotePath=false"] + args,
                              capture_output=True, text=True, cwd=ROOT, timeout=_GIT_TIMEOUT)
    except subprocess.TimeoutExpired:
        DATE_ERRORS.append(f"{what}: git timed out after {_GIT_TIMEOUT}s")
        return None
    except OSError as exc:  # git not on PATH, ROOT unreadable
        DATE_ERRORS.append(f"{what}: git could not run ({exc})")
        return None
    if proc.returncode != 0:
        tail = proc.stderr.strip().splitlines()
        DATE_ERRORS.append(f"{what}: git exited {proc.returncode}"
                           + (f" ({tail[-1]})" if tail else ""))
        return None
    return proc.stdout


def tracked_files():
    """Every path in the git index. Reads the index only — no object reads, so
    this stays fast even when the object store is cold."""
    global _TRACKED
    if _TRACKED is None:
        out = _git(["ls-files"], "index scan")
        _TRACKED = {ln.strip() for ln in (out or "").splitlines() if ln.strip()}
    return _TRACKED


def last_updated(path: Path) -> str:
    """Date of the last commit touching this path (needs full clone: fetch-depth 0 in CI).

    Falling back to today's date is only correct when the path has no commits
    yet. When git itself fails, today's date is a guess, so it goes in
    DATE_ERRORS and main() reports it (and exits non-zero under --strict);
    silently guessing publishes a wrong "updated" date to the live site, since
    CI commits the regenerated catalog back to master.

    The index is checked first because `git log -1 -- <path>` walks the *entire*
    history whenever nothing matches the pathspec — measured at ~27s here
    against 0.03s for a committed path, which blew the old 10s timeout and was
    then swallowed by a bare `except`. That was the silent-guess bug. Checking
    the index costs one cheap call and skips the walk for paths that can't match.
    """
    key = str(path)
    if key in _DATE_CACHE:
        return _DATE_CACHE[key]
    rel = _rel(path)
    today = date.today().isoformat()
    prefix = rel + "/"
    result = ""
    if any(f == rel or f.startswith(prefix) for f in tracked_files()):
        result = (_git(["log", "-1", "--format=%cs", "--", str(path)],
                       f"{rel}: last-commit date") or "").strip()
    if not result:
        result = today
        # Only genuinely "no commits" if every git call so far actually worked.
        if not DATE_ERRORS:
            DATE_UNTRACKED.append(rel)
    _DATE_CACHE[key] = result
    return result

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

# --- Faculty-facing help copy (single source of truth) ----------------------
# Every explanation on the site comes from here, so the catalogs, the tooltips,
# and start-here.html can never disagree with each other.

GLOSSARY = {
    "Skill": {
        "icon": "🧩",
        "short": "A set of instructions you add to Claude or ChatGPT so it handles one task the McCombs way.",
        "long": ("A skill is a short instruction file you upload once. After that there is no command to "
                 "remember — you ask for the task in your own words and the assistant follows the recipe "
                 "automatically. Most things in this catalog are skills."),
        "when": "Use a skill when you want help with one specific job, like writing a case or building a rubric.",
    },
    "Plug-in": {
        "icon": "📦",
        "short": "A bundle of related skills that installs in one step and updates itself in Claude.",
        "long": ("A plug-in packages several skills that work together. Installing it adds all of them at once, "
                 "and in Claude it keeps itself up to date, so you don't have to re-download when we improve "
                 "a skill. ChatGPT doesn't support plug-ins — there you upload the skills individually."),
        "when": "Use a plug-in when you want the whole set for a workflow rather than picking skills one at a time.",
    },
    "Artifact": {
        "icon": "⚡",
        "short": "A small interactive tool that runs as its own page in Claude.",
        "long": ("An artifact isn't installed into the assistant — it's a little web app you open and use, with "
                 "its own buttons and chat box. You publish the file once in Claude and then just open the link."),
        "when": "Use an artifact when you want a hands-on tool rather than something that answers inside a chat.",
    },
}

# Plain-English gloss for each compatibility badge, keyed by classification.
BADGE_HELP = {
    "both": "Works the same in UT Claude EDU and the UT ChatGPT workspace.",
    "both-with-caveats": ("Works in both, with small differences on ChatGPT. The “Good to know” section on the "
                          "skill's page explains exactly what changes."),
    "claude-code-only": ("Runs command-line software (things like LaTeX) that has to be installed on your own "
                         "computer. Best used in Claude Code — it won't work on the Claude or ChatGPT websites."),
    "claude-only": "Uses Claude features that ChatGPT doesn't have, so it isn't available for ChatGPT.",
}

PLATFORM_HELP = ("Where you can use this. “Claude” means UT Claude EDU (the website or desktop app); "
                 "“ChatGPT” means the UT ChatGPT workspace.")

TIP_ID = [0]


def tooltip(text: str, label: str = "?") -> str:
    """A small accessible help button. Opens on hover, click (touch), or keyboard; Esc closes."""
    TIP_ID[0] += 1
    tid = f"tip{TIP_ID[0]}"
    return (f'<span class="hintwrap"><button type="button" class="hint" aria-describedby="{tid}" '
            f'aria-label="What does this mean?">{label}</button>'
            f'<span role="tooltip" id="{tid}" class="tip">{html.escape(text)}</span></span>')

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
/* --- help: tooltips --- */
.hintwrap{position:relative;display:inline-block;line-height:1}
.hint{width:15px;height:15px;padding:0;border-radius:50%;border:1px solid var(--line);
  background:var(--surface);color:var(--muted);font-size:10.5px;font-weight:700;cursor:help;
  vertical-align:1px;margin-left:5px;font-family:inherit}
.hint:hover,.hint[aria-expanded="true"]{border-color:var(--accent);color:var(--accent-deep)}
.hint:focus-visible{outline:2px solid var(--accent);outline-offset:2px}
.tip{position:absolute;z-index:20;left:0;top:calc(100% + 7px);width:max-content;max-width:min(270px,72vw);
  background:var(--ink);color:var(--bg);border-radius:8px;padding:9px 12px;font-size:12.5px;
  line-height:1.45;font-weight:400;text-transform:none;letter-spacing:0;display:none;
  white-space:normal;text-align:left;box-shadow:0 4px 14px rgba(0,0,0,.22)}
.tip.on{display:block}
.hintwrap:hover .tip{display:block}
/* --- help: intro strip --- */
.intro{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:16px 20px;margin:18px 0 4px;
  box-shadow:var(--shadow)}
.intro h2{margin:0 0 3px;font-size:18px}
.intro .lede{margin:0 0 12px;font-size:13.5px;color:var(--muted);max-width:70ch}
.intro .kinds{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:10px;margin-bottom:12px}
.kind{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:11px 14px}
.kind b{display:block;font-size:14px;margin-bottom:2px}
.kind span{font-size:12.5px;color:var(--muted);line-height:1.45}
.intro .more{font-size:13.5px}
.intro .close{float:right;background:none;border:1px solid var(--line);border-radius:7px;color:var(--muted);
  font-size:12px;padding:3px 10px;cursor:pointer;margin-left:12px}
.intro .close:hover{border-color:var(--accent);color:var(--accent-deep)}
.introbar{display:none;margin:16px 0 0}
.introbar button{background:var(--surface);border:1px solid var(--line);border-radius:8px;color:var(--accent-deep);
  font-size:13px;padding:7px 14px;cursor:pointer;font-weight:600;font-family:inherit}
.introbar button:hover{border-color:var(--accent)}
body.introhid .intro{display:none} body.introhid .introbar{display:block}
/* --- help: example prompts --- */
.ex{display:flex;gap:10px;align-items:center;background:var(--bg);border:1px solid var(--line);
  border-radius:8px;padding:9px 13px;margin:6px 0;font-size:13.5px}
.ex button{margin-left:auto;flex-shrink:0;background:var(--surface);border:1px solid var(--line);border-radius:6px;
  color:var(--accent-deep);font-size:12px;padding:4px 10px;cursor:pointer;font-family:inherit}
.ex button:hover{border-color:var(--accent)}
.howto{font-size:13px;color:var(--muted);margin:0 0 8px;max-width:68ch}
/* --- help: start-here page --- */
.sh h2{font-size:21px;margin:28px 0 8px;padding-bottom:5px;border-bottom:2px solid var(--accent)}
.sh h3{font-size:16px;margin:18px 0 5px}
.sh p,.sh li{font-size:14.5px;line-height:1.6;max-width:70ch}
.sh table{width:100%;border-collapse:collapse;margin:10px 0;font-size:13.5px;display:block;overflow-x:auto}
.sh td,.sh th{border:1px solid var(--line);padding:8px 11px;text-align:left;vertical-align:top}
.sh th{background:var(--surface);font-size:12px;text-transform:uppercase;letter-spacing:.05em;color:var(--accent-deep)}
.sh ol li{margin:5px 0}
.toc{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0 4px}
.toc a{font-size:13px;border:1px solid var(--line);border-radius:18px;padding:5px 13px;text-decoration:none;
  background:var(--surface)}
.toc a:hover{border-color:var(--accent)}
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


# --- Option C prototype (docs/option-c.html) -------------------------------
# A dense, filterable index served alongside the live catalog so faculty can
# compare layouts. Generated from the same data, so it can never drift.

CSS_C = """
.protobar{background:var(--accent-soft);border-bottom:1px solid var(--line);font-size:12.5px;padding:7px 0}
.protobar .wrap{display:flex;gap:10px;align-items:baseline;flex-wrap:wrap}
.protobar a{margin-left:auto}
.cols{display:flex;gap:22px;align-items:flex-start;margin-top:18px}
aside{width:218px;flex-shrink:0;position:sticky;top:12px}
.fgroup{background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin-bottom:10px}
.fgroup h3{margin:0 0 8px;font-size:11.5px;text-transform:uppercase;letter-spacing:.07em;color:var(--accent-deep);font-family:inherit}
.fgroup label{display:flex;gap:7px;align-items:center;font-size:13px;padding:2.5px 0;cursor:pointer}
.fgroup label .n{margin-left:auto;color:var(--muted);font-size:11.5px;font-variant-numeric:tabular-nums}
.fgroup input{accent-color:var(--accent)}
.reset{width:100%;background:none;border:1px solid var(--line);border-radius:8px;color:var(--muted);
  font-size:12.5px;padding:6px;cursor:pointer}
.reset:hover{border-color:var(--accent);color:var(--accent-deep)}
section.list{flex:1;min-width:0}
.tablewrap{overflow-x:auto}
.listtop{display:flex;gap:10px;align-items:center;margin-bottom:10px;flex-wrap:wrap}
table{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--line);border-radius:10px;overflow:hidden}
thead th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);text-align:left;
  padding:9px 12px;border-bottom:2px solid var(--line);white-space:nowrap;background:var(--surface)}
thead th[data-k]{cursor:pointer;user-select:none}
thead th.on{color:var(--accent-deep)}
tbody tr.row{border-top:1px solid var(--line);cursor:pointer}
tbody tr.row:hover{background:var(--accent-soft)}
td{padding:8px 12px;vertical-align:baseline;font-size:13.5px}
td.name{font-weight:600;white-space:nowrap;font-size:14px}
td.date{white-space:nowrap;font-variant-numeric:tabular-nums;color:var(--muted);font-size:12.5px}
td.cat{color:var(--muted);font-size:12.5px}
.tp{font-size:11.5px;font-weight:600;border-radius:5px;padding:1.5px 7px;white-space:nowrap;
  color:var(--tone);background:color-mix(in srgb,var(--tone) 12%,transparent)}
.tp.skill{--tone:var(--ok)}.tp.plugin{--tone:var(--accent-deep)}.tp.artifact{--tone:var(--claude)}
.works{display:flex;gap:6px;flex-wrap:wrap;align-items:center;font-size:12.5px;color:var(--muted)}
.works .no{opacity:.45;text-decoration:line-through}
.works .gear{cursor:help}
tr.xp td{padding:0}
.xpbox{background:var(--bg);border-top:1px dashed var(--line);padding:14px 18px;font-size:13.5px}
.xpbox .actions{display:flex;gap:14px;flex-wrap:wrap;margin-top:8px;font-size:13px;align-items:baseline}
.xpbox .meta2{color:var(--muted);font-size:12.5px}
.empty{text-align:center;color:var(--muted);padding:40px 0}
@media (max-width:760px){.cols{flex-direction:column;align-items:stretch}
  aside{width:100%;position:static}
  section.list{width:100%}
  thead .hide-sm,td.hide-sm{display:none}}
"""

TYPE_ORDER = ["Skill", "Plug-in", "Artifact"]


def catalog_entries(report, artifacts):
    """One flat row model covering all three kinds, for the Option C index."""
    entries = []
    for r in report:
        cls = r["classification"]
        entries.append({
            "name": r["skill"], "title": r["skill"], "type": "Skill",
            "category": r.get("category", "General"), "summary": summary_of(r),
            "chatgpt": cls in ("both", "both-with-caveats"),
            "local": cls == "claude-code-only",
            "updated": last_updated(ROOT / "plugins" / r["plugin"] / "skills" / r["skill"]),
            "version": str(r["version"]) if r.get("version") else "",
            "href": f"skills/{r['skill']}.html",
            "zip": ZIP_URL.format(skill=r["skill"]),
            "extra": r["plugin"],
        })

    # Plug-ins: same qualifying rule as toolkit_bands() — needs a toolkits/<name>/ source tree.
    manifest = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    by_plugin = {}
    for r in report:
        by_plugin.setdefault(r["plugin"], []).append(r)
    for p in manifest["plugins"]:
        members = by_plugin.get(p["name"])
        if not members or not (ROOT / "toolkits" / p["name"]).is_dir():
            continue
        pj = json.loads((ROOT / "plugins" / p["name"] / ".claude-plugin" / "plugin.json").read_text())
        ver = pj.get("version", "?")
        # Category = the most common category among member skills (ties broken by CATEGORY_ORDER).
        counts = {}
        for m in members:
            counts[m.get("category", "General")] = counts.get(m.get("category", "General"), 0) + 1
        cat = sorted(counts, key=lambda c: (-counts[c], CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99))[0]
        entries.append({
            "name": p["name"], "title": p["name"], "type": "Plug-in", "category": cat,
            "summary": p["description"], "chatgpt": True, "local": False,
            "updated": last_updated(ROOT / "plugins" / p["name"]),
            "version": ver, "href": f"toolkits/{p['name']}.html",
            "zip": ZIP_URL.format(skill=f"{p['name']}-v{ver}"),
            "chatgpt_zip": ZIP_URL.format(skill=f"{p['name']}-chatgpt-v{ver}"),
            "extra": f"{len(members)} skills",
        })

    for a in artifacts:
        entries.append({
            "name": a["name"], "title": a["title"], "type": "Artifact",
            "category": a.get("category", "General"), "summary": a["summary"],
            "chatgpt": False, "local": False, "updated": last_updated(a["dir"]),
            "version": str(a.get("version", "")), "href": f"artifacts/{a['name']}.html",
            "download": f"artifacts/files/{a['file']}",
            "extra": a.get("platform", "Claude"),
        })
    return entries


def option_c_row(e):
    tone = {"Skill": "skill", "Plug-in": "plugin", "Artifact": "artifact"}[e["type"]]
    gpt = ('<span>ChatGPT</span>' if e["chatgpt"] else '<span class="no">ChatGPT</span>')
    gear = (f'<span class="gear">⚙{tooltip(BADGE_HELP["claude-code-only"])}</span>' if e["local"] else "")
    if e["type"] == "Skill":
        links = (f'<a href="{e["zip"]}">⬇ Claude zip</a>'
                 + (f'<a href="{e["zip"]}">⬇ ChatGPT zip</a>' if e["chatgpt"]
                    else '<span class="meta2">ChatGPT: not available</span>'))
        if e["local"]:
            links = (f'<span>Claude Code: <code>/plugin marketplace add {REPO_SLUG}</code> '
                     f'or <a href="{e["zip"]}">zip</a> → <code>~/.claude/skills/</code></span>')
    elif e["type"] == "Plug-in":
        links = (f'<span>Claude: <code>/plugin marketplace add {REPO_SLUG}</code></span>'
                 f'<a href="{e["zip"]}">⬇ Claude zip</a><a href="{e["chatgpt_zip"]}">⬇ ChatGPT zip</a>')
    else:
        links = f'<a href="{e["download"]}" download>⬇ Download .html</a><span class="meta2">publish it as an artifact in Claude</span>'
    ver = f' &middot; v{html.escape(e["version"])}' if e["version"] and e["type"] != "Artifact" else (
        f' &middot; {html.escape(e["version"])}' if e["version"] else "")
    return f"""<tr class="row" data-id="{html.escape(e['name'])}" data-type="{e['type']}"
  data-category="{html.escape(e['category'])}" data-gpt="{'1' if e['chatgpt'] else ''}"
  data-name="{html.escape(e['name'])}" data-updated="{e['updated']}" tabindex="0">
  <td class="name">{html.escape(e['title'])}</td>
  <td><span class="tp {tone}">{e['type']}</span></td>
  <td class="cat hide-sm">{html.escape(e['category'])}</td>
  <td><div class="works"><span>Claude</span>{gpt}{gear}</div></td>
  <td class="date hide-sm">{e['updated']}</td></tr>
<tr class="xp" data-for="{html.escape(e['name'])}" hidden><td colspan="5"><div class="xpbox">
  {html.escape(e['summary'])}
  <div class="actions">{links}<a href="{e['href']}">Full details →</a>
  <span class="meta2">{html.escape(e['extra'])}{ver}</span></div>
</div></td></tr>"""


def option_c_page(entries):
    """Write docs/option-c.html — the dense filterable index prototype."""
    def count(pred):
        return sum(1 for e in entries if pred(e))
    types = [t for t in TYPE_ORDER if count(lambda e, t=t: e["type"] == t)]
    cats = sorted({e["category"] for e in entries},
                  key=lambda c: (CATEGORY_ORDER.index(c) if c in CATEGORY_ORDER else 99, c))
    rows = "".join(option_c_row(e) for e in
                   sorted(entries, key=lambda e: (e["name"].lower())))
    n = len(entries)
    type_f = "".join(
        f'<label><input type="checkbox" data-g="type" value="{t}">{t}s'
        f'<span class="n">{count(lambda e, t=t: e["type"] == t)}</span></label>' for t in types)
    cat_f = "".join(
        f'<label><input type="checkbox" data-g="cat" value="{html.escape(c)}">{html.escape(c)}'
        f'<span class="n">{count(lambda e, c=c: e["category"] == c)}</span></label>' for c in cats)
    works_f = (f'<label><input type="checkbox" data-g="works" value="claude">Claude'
               f'<span class="n">{n}</span></label>'
               f'<label><input type="checkbox" data-g="works" value="chatgpt">ChatGPT'
               f'<span class="n">{count(lambda e: e["chatgpt"])}</span></label>')
    header = ('<h1>McCombs AI Skills</h1>'
              '<p>Ready-made AI tools for teaching and learning at McCombs</p>')
    protobar = """<div class="protobar"><div class="wrap"><b>Prototype layout</b>
<span>A denser alternative to the main catalog — we'd love your feedback on which works better.</span>
<a href="index.html">← Back to the main catalog</a></div></div>
"""
    body = f"""<main class="wrap">
{help_strip()}
<div class="cols">
<aside>
  <div class="fgroup"><h3>Type{tooltip("Skills and plug-ins are added to Claude or ChatGPT; artifacts are interactive tools you open in Claude.")}</h3>{type_f}</div>
  <div class="fgroup"><h3>Category{tooltip("The kind of teaching work each item helps with.")}</h3>{cat_f}</div>
  <div class="fgroup"><h3>Works in{tooltip(PLATFORM_HELP)}</h3>{works_f}</div>
  <button class="reset" id="reset">Reset filters</button>
</aside>
<section class="list">
  <div class="listtop">
    <input id="q" type="search" placeholder="Filter {n} skills, plug-ins &amp; artifacts…">
    <span class="count" id="count">{n} shown &middot; {n} total</span></div>
  <p style="font-size:12.5px;color:var(--muted);margin:0 0 8px">Click any row to see what it does and how to install it.</p>
  <div class="tablewrap"><table><thead><tr>
    <th data-k="name">Name</th>
    <th data-k="type">Type</th>
    <th data-k="category" class="hide-sm">Category</th>
    <th>Works in</th>
    <th data-k="updated" class="hide-sm">Updated</th></tr></thead>
  <tbody id="tb">{rows}</tbody></table></div>
  <div class="empty" id="empty" hidden>Nothing matches those filters. <a href="#" id="reset2">Reset filters</a></div>
  <footer>Maintained by the McCombs AI Faculty Working Group &middot;
  <a href="start-here.html">Start here guide</a> &middot;
  <a href="{REPO_URL}/blob/master/CONTRIBUTING.md">How to contribute or update a skill</a> &middot; ⚙ = runs software you install locally</footer>
</section></div></main>
<script>{JS_C}</script>
<script>{JS_HELP}</script>"""
    out = ROOT / "docs" / "option-c.html"
    out.write_text(page_shell("Index (prototype)", body, header, CSS_C, protobar))
    print(f"Wrote {out.relative_to(ROOT)} ({n} entries)")


JS_C = """
const tb=document.getElementById('tb'), q=document.getElementById('q');
const countEl=document.getElementById('count'), empty=document.getElementById('empty');
const rows=[...tb.querySelectorAll('tr.row')];
const state={type:new Set(),cat:new Set(),works:new Set(),sort:['',1],open:null};
function apply(){
  const v=q.value.toLowerCase();
  let shown=0;
  rows.forEach(r=>{
    const xp=tb.querySelector(`tr.xp[data-for="${CSS.escape(r.dataset.id)}"]`);
    const ok=(!state.type.size||state.type.has(r.dataset.type))
      &&(!state.cat.size||state.cat.has(r.dataset.category))
      &&(!state.works.size||[...state.works].every(w=>w==='claude'||r.dataset.gpt))
      &&(r.textContent+' '+xp.textContent).toLowerCase().includes(v);
    r.hidden=!ok; if(ok)shown++;
    xp.hidden=!ok||state.open!==r.dataset.id;
  });
  countEl.textContent=`${shown} shown \\u00b7 ${rows.length} total`;
  empty.hidden=shown>0;
}
function sortBy(k){
  state.sort=state.sort[0]===k?[k,-state.sort[1]]:[k,1];
  const [key,dir]=state.sort;
  const val=r=>(r.dataset[key]||'').toLowerCase();
  const flip=key==='updated'?-1:1;   // dates open newest-first; text opens A-Z
  [...rows]
    .sort((a,b)=>dir*flip*val(a).localeCompare(val(b))||a.dataset.name.localeCompare(b.dataset.name))
    .forEach(r=>{tb.appendChild(r);tb.appendChild(tb.querySelector(`tr.xp[data-for="${CSS.escape(r.dataset.id)}"]`))});
  document.querySelectorAll('thead th[data-k]').forEach(th=>{
    th.classList.toggle('on',th.dataset.k===key);
    th.textContent=th.textContent.replace(/ [\\u2191\\u2193]$/,'')
      +(th.dataset.k===key?(dir*flip>0?' \\u2191':' \\u2193'):'');
  });
}
q.addEventListener('input',apply);
document.querySelectorAll('aside input').forEach(i=>i.addEventListener('change',()=>{
  const set=state[i.dataset.g]; i.checked?set.add(i.value):set.delete(i.value); apply();
}));
document.querySelectorAll('thead th[data-k]').forEach(th=>th.addEventListener('click',()=>sortBy(th.dataset.k)));
function toggle(r){ state.open=state.open===r.dataset.id?null:r.dataset.id; apply(); }
rows.forEach(r=>{
  r.addEventListener('click',()=>toggle(r));
  r.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();toggle(r);}});
});
tb.querySelectorAll('tr.xp a').forEach(a=>a.addEventListener('click',e=>e.stopPropagation()));
function reset(e){
  if(e)e.preventDefault();
  ['type','cat','works'].forEach(g=>state[g].clear());
  document.querySelectorAll('aside input').forEach(i=>i.checked=false);
  q.value=''; apply();
}
document.getElementById('reset').addEventListener('click',()=>reset());
document.getElementById('reset2').addEventListener('click',reset);
sortBy('name');
"""


# Shared behavior for every page: tooltips, copy-to-clipboard, intro strip.
JS_HELP = """
// Keep a tooltip inside the viewport regardless of where its trigger sits.
function placeTip(tip){
  tip.style.transform='';
  // clientWidth = layout viewport (excludes scrollbar); innerWidth would let tips slide off-screen.
  const vw=document.documentElement.clientWidth, r=tip.getBoundingClientRect(), pad=8;
  let dx=0;
  if(r.right>vw-pad)dx=vw-pad-r.right;
  if(r.left+dx<pad)dx=pad-r.left;
  if(dx)tip.style.transform='translateX('+Math.round(dx)+'px)';
}
document.querySelectorAll('.hint').forEach(b=>{
  const tip=document.getElementById(b.getAttribute('aria-describedby'));
  const close=()=>{tip.classList.remove('on');b.setAttribute('aria-expanded','false');};
  b.setAttribute('aria-expanded','false');
  b.addEventListener('mouseenter',()=>placeTip(tip));
  b.addEventListener('click',e=>{
    e.preventDefault();e.stopPropagation();
    const open=tip.classList.contains('on');
    document.querySelectorAll('.tip.on').forEach(t=>t.classList.remove('on'));
    document.querySelectorAll('.hint').forEach(h=>h.setAttribute('aria-expanded','false'));
    if(!open){tip.classList.add('on');b.setAttribute('aria-expanded','true');placeTip(tip);}
  });
  b.addEventListener('focus',()=>{tip.classList.add('on');placeTip(tip);});
  b.addEventListener('blur',close);
});
document.addEventListener('keydown',e=>{if(e.key==='Escape'){
  document.querySelectorAll('.tip.on').forEach(t=>t.classList.remove('on'));
  document.querySelectorAll('.hint').forEach(h=>h.setAttribute('aria-expanded','false'));}});
document.addEventListener('click',()=>{
  document.querySelectorAll('.tip.on').forEach(t=>t.classList.remove('on'));
  document.querySelectorAll('.hint').forEach(h=>h.setAttribute('aria-expanded','false'));});
document.querySelectorAll('.ex button').forEach(b=>b.addEventListener('click',e=>{
  e.preventDefault();e.stopPropagation();
  const txt=b.parentElement.querySelector('span').textContent.replace(/^[\\u201c"]|[\\u201d"]$/g,'');
  if(navigator.clipboard)navigator.clipboard.writeText(txt);
  const was=b.textContent;b.textContent='Copied \\u2713';setTimeout(()=>b.textContent=was,1300);
}));
(function(){
  const KEY='mccombs-intro-seen';
  const intro=document.querySelector('.intro');
  if(!intro)return;
  try{if(localStorage.getItem(KEY))document.body.classList.add('introhid');}catch(e){}
  const hide=()=>{document.body.classList.add('introhid');try{localStorage.setItem(KEY,'1');}catch(e){}};
  const show=()=>{document.body.classList.remove('introhid');try{localStorage.removeItem(KEY);}catch(e){}};
  const c=intro.querySelector('.close'); if(c)c.addEventListener('click',hide);
  const o=document.querySelector('.introbar button'); if(o)o.addEventListener('click',show);
})();
"""


def help_strip() -> str:
    """The dismissible 'New to AI skills?' explainer shown on both catalog pages."""
    kinds = "".join(
        f'<div class="kind"><b>{g["icon"]} {name}</b><span>{html.escape(g["short"])}</span></div>'
        for name, g in GLOSSARY.items())
    return f"""<div class="intro">
  <button class="close" type="button">Hide this</button>
  <h2>New to AI skills?</h2>
  <p class="lede">Everything below is something you add to the AI you already use — UT Claude EDU or the
  UT ChatGPT workspace. Installing takes about a minute, and afterwards you just ask for what you want
  in your own words.</p>
  <div class="kinds">{kinds}</div>
  <p class="more"><a href="start-here.html">Read the full 5-minute guide &rarr;</a></p>
</div>
<div class="introbar"><button type="button">New to AI skills? Read the 1-minute intro</button></div>"""


def examples_panel(examples, kind="skill") -> str:
    """'Try saying…' prompts — the answer to 'I installed it, now what?'"""
    if not examples:
        return ""
    if kind == "artifact":
        howto = "Once the artifact is open, try asking it something like:"
    else:
        howto = ("Once it's installed there's no command to remember — just ask for what you want. "
                 "These are the kinds of requests that put this skill to work:")
    rows = "".join(
        f'<div class="ex"><span>“{html.escape(x)}”</span><button type="button">Copy</button></div>'
        for x in examples)
    return f'<div class="panel"><h3>Try saying…</h3><p class="howto">{howto}</p>{rows}</div>'


def summary_of(r) -> str:
    """metadata.summary, or the description truncated at a sentence/word boundary."""
    if r.get("summary"):
        return r["summary"]
    desc = r.get("description", "")
    first = re.split(r"(?<=[.!?])\s", desc, 1)[0]
    if len(first) <= 160:
        return first
    return first[:157].rsplit(" ", 1)[0] + "…"


def platform_marks(cls: str, with_help: bool = False) -> str:
    gpt_ok = cls in ("both", "both-with-caveats")
    marks = ["<span>Claude ✓</span>",
             f"<span class=\"{'' if gpt_ok else 'no'}\">ChatGPT{' ✓' if gpt_ok else ''}</span>"]
    if cls == "claude-code-only":
        marks.append(f'<span>⚙ local software{tooltip(BADGE_HELP["claude-code-only"])}</span>')
    elif with_help:
        marks.append(tooltip(PLATFORM_HELP))
    return f"<div class='plats'>{''.join(marks)}</div>"


def badge(cls: str, with_help: bool = False) -> str:
    label, tone = BADGES[cls]
    tip = tooltip(BADGE_HELP[cls]) if with_help else ""
    return f"<span class='badge {tone}'>{label}{tip}</span>"


def page_shell(title: str, body: str, header: str, extra_css: str = "", pre_header: str = "") -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — McCombs AI Skills</title><style>{CSS}{extra_css}</style></head><body>
{pre_header}<header class="site"><div class="wrap">{header}</div></header>
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
  <div class="meta">{badge(cls, with_help=True)}{ver}<span>&middot;</span><span>{html.escape(r['plugin'])}</span></div>
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
    header = ("<h1>McCombs AI Skills</h1><p>Ready-to-use AI skills for teaching and learning &middot; "
              "<a href=\"../start-here.html\">New here? Start with the guide</a></p>")
    body = f"""<main class="wrap detail">
<a class="back" href="../index.html">← All skills</a>
<div class="dhead"><div class="meta" style="margin-bottom:6px">{badge(r['classification'], with_help=True)}
  <span>{html.escape(r.get('category', 'General'))}</span><span>&middot;</span>
  <span>{html.escape(r['plugin'])}</span><span>&middot;</span>
  {ver}<span>updated {updated}</span></div>
  <h2>{html.escape(r['skill'])}</h2><p class="sum">{html.escape(summary_of(r))}</p></div>
<div class="install"><h3>Install{tooltip("Not sure which platform is which? The Start here guide walks through each one.")}</h3>{install_accordions(r)}</div>
{examples_panel(r.get("examples") or [])}
{notes_html}
<div class="panel"><h3>About this skill</h3>
<p style="font-size:12.5px;color:var(--muted);margin:0 0 10px">The content below is {source_note}.</p>
<div class="doc">{render_md(src)}</div></div>
<details class="acc"><summary>Files included<span class="tag">{len(files)}</span></summary>
<div class="body"><ul>{file_list}</ul></div></details>
<a class="back" href="../index.html">← All skills</a>
<footer style="border:none;padding-top:8px">McCombs AI Skills &middot;
<a href="../start-here.html">Start here guide</a> &middot;
<a href="{REPO_URL}/blob/master/CONTRIBUTING.md">How to contribute or update a skill</a></footer>
</main>
<script>{JS_HELP}</script>"""
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
    header = ("<h1>McCombs AI Skills</h1><p>Ready-to-use AI skills for teaching and learning &middot; "
              "<a href=\"../start-here.html\">New here? Start with the guide</a></p>")
    body = f"""<main class="wrap detail">
<a class="back" href="../index.html">← All skills</a>
<div class="dhead"><div class="meta" style="margin-bottom:6px"><span class='badge ok'>Plug-in{tooltip(GLOSSARY['Plug-in']['long'])}</span>
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
<footer style="border:none;padding-top:8px">McCombs AI Skills &middot;
<a href="../start-here.html">Start here guide</a> &middot; <a href="{REPO_URL}">GitHub repository</a></footer>
</main>
<script>{JS_HELP}</script>"""
    out = ROOT / "docs" / "toolkits" / f"{name}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page_shell(name, body, header))


def load_artifacts():
    """Artifacts are interactive HTML tools under artifacts/<name>/, described by artifact.json.
    Unlike skills they have no SKILL.md or zip — the HTML file itself is the deliverable,
    and they run only where Claude can publish/host artifacts (Cowork, claude.ai)."""
    out = []
    for aj in sorted((ROOT / "artifacts").glob("*/artifact.json")):
        a = json.loads(aj.read_text())
        a["dir"] = aj.parent
        a.setdefault("category", "General")
        out.append(a)
    return out


def artifact_card(a):
    updated = last_updated(a["dir"])
    artifact_detail_page(a, updated)
    dst = ROOT / "docs" / "artifacts" / "files" / a["file"]
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(a["dir"] / a["file"], dst)
    ver = f"<span>{html.escape(str(a['version']))}</span><span>&middot;</span>" if a.get("version") else ""
    return f"""
<div class="card" data-category="Artifacts" data-name="{html.escape(a['name'])}" data-updated="{updated}">
  <h3><a href="artifacts/{a['name']}.html">{html.escape(a['title'])}</a></h3>
  <p class="sum">{html.escape(a['summary'])}</p>
  <div class="meta"><span class='badge claude'>{html.escape(a.get('platform', 'Claude'))} only</span>{ver}<span>artifact</span></div>
  <div class='plats'><span>{html.escape(a.get('platform', 'Claude'))} ✓</span><span class="no">ChatGPT</span></div>
</div>"""


def artifact_detail_page(a, updated):
    """Write docs/artifacts/<name>.html — what it does and how to run it in Claude."""
    name = html.escape(a["name"])
    file_link = f"files/{a['file']}"
    ver = f"<span class='mono'>{html.escape(str(a['version']))}</span><span>&middot;</span>" if a.get("version") else ""
    open_btn = (f"<p><a class='btn' href='{html.escape(a['link'])}'>Open {html.escape(a['title'])} →</a>"
                f"<span style='font-size:12.5px;color:var(--muted);margin-left:10px'>opens the shared artifact in Claude</span></p>"
                if a.get("link") else "")
    header = ("<h1>McCombs AI Skills</h1><p>Ready-to-use AI skills for teaching and learning &middot; "
              "<a href=\"../start-here.html\">New here? Start with the guide</a></p>")
    body = f"""<main class="wrap detail">
<a class="back" href="../index.html">← All skills</a>
<div class="dhead"><div class="meta" style="margin-bottom:6px"><span class='badge claude'>{html.escape(a.get('platform', 'Claude'))} only{tooltip(GLOSSARY['Artifact']['long'])}</span>
  <span>Artifact</span><span>&middot;</span>{ver}<span>updated {updated}</span></div>
  <h2>{html.escape(a['title'])}</h2><p class="sum">{html.escape(a['summary'])}</p></div>
<div class="install"><h3>Use it</h3>
{open_btn}
<details class="acc" open><summary>🟠 Run it in Claude Cowork<span class="tag">~2 minutes, once</span></summary>
<div class="body"><ol>
<li><a href="{file_link}" download>Download {html.escape(a['file'])}</a>.</li>
<li>In <b>Claude Cowork</b>, add the file to your session (attach it or drop it in the project folder).</li>
<li>Ask Claude to <i>“publish this file as an artifact”</i> — it returns a private link you can open, bookmark, and share.</li>
</ol>
<p>The built-in chat only connects when the page runs as a Claude artifact —
<a href="{file_link}">previewing the file directly</a> shows the interface, but messages won't send.</p></div></details>
<div class="acc unavail"><div class="head">⚪ ChatGPT<span class="tag">Not available — artifacts run on Claude only</span></div></div>
</div>
{examples_panel(a.get("examples") or [], kind="artifact")}
<div class="panel"><h3>About this artifact</h3>
<p style="font-size:14px;line-height:1.55">{html.escape(a['description'])}</p>
{f"<p style='font-size:12.5px;color:var(--muted)'>Created by {html.escape(a['author'])}.</p>" if a.get('author') else ""}</div>
<a class="back" href="../index.html">← All skills</a>
<footer style="border:none;padding-top:8px">McCombs AI Skills &middot;
<a href="../start-here.html">Start here guide</a> &middot;
<a href="{REPO_URL}/blob/master/CONTRIBUTING.md">How to contribute or update a skill</a></footer>
</main>
<script>{JS_HELP}</script>"""
    out = ROOT / "docs" / "artifacts" / f"{a['name']}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page_shell(a["title"], body, header))


def start_here_page():
    """Write docs/start-here.html — the plain-English guide for faculty new to all of this."""
    kinds = "".join(
        f'<h3>{g["icon"]} {name}</h3><p>{html.escape(g["long"])}</p>'
        f'<p style="color:var(--muted);font-size:13.5px"><b>When to pick one:</b> {html.escape(g["when"])}</p>'
        for name, g in GLOSSARY.items())
    badges = "".join(
        f'<tr><td><span class="badge {BADGES[k][1]}">{BADGES[k][0]}</span></td><td>{html.escape(v)}</td></tr>'
        for k, v in BADGE_HELP.items())
    header = ('<h1>Start here</h1>'
              '<p>A five-minute guide to using AI skills at McCombs — no technical background needed</p>')
    body = f"""<main class="wrap detail sh" style="max-width:820px">
<a class="back" href="index.html">← Back to the catalog</a>
<div class="toc">
  <a href="#kinds">What's on this site</a><a href="#where">Where things go</a>
  <a href="#install">Installing</a><a href="#using">Using it afterwards</a>
  <a href="#badges">What the badges mean</a><a href="#trouble">If something doesn't work</a></div>

<h2 id="kinds">What's on this site</h2>
<p>The catalog holds three kinds of thing. They all make the AI better at a specific job — the difference
is how you get to them.</p>
{kinds}

<h2 id="where">Where these go</h2>
<p>You don't need any new software. Everything installs into a tool UT already provides.</p>
<table><thead><tr><th>Where</th><th>What it is</th><th>What it can use</th></tr></thead><tbody>
<tr><td><b>Claude (UT Claude EDU)</b></td><td>The Claude website or desktop app you sign in to with your UT account.</td>
  <td>Skills, plug-ins, and artifacts — everything here.</td></tr>
<tr><td><b>ChatGPT (UT workspace)</b></td><td>The ChatGPT workspace provided through UT.</td>
  <td>Most skills. Not plug-ins or artifacts, and not skills marked Claude only.</td></tr>
<tr><td><b>Claude Code</b></td><td>A version of Claude that runs on your own computer. Only needed for a few
  skills that use software installed locally.</td><td>Everything, including skills marked “Needs local software”.</td></tr>
</tbody></table>

<h2 id="install">Installing, step by step</h2>
<h3>A single skill, in Claude</h3>
<ol><li>On the skill's page in the catalog, click <b>Download <span class="mono">&lt;name&gt;.zip</span></b>.
  Leave it zipped — don't unzip it.</li>
<li>In Claude, open <b>Settings → Capabilities → Skills</b>.</li>
<li>Click <b>Upload skill</b> and choose the .zip file you just downloaded.</li>
<li>That's it. The skill is now available in every new conversation.</li></ol>
<h3>A single skill, in ChatGPT</h3>
<ol><li>Download the same .zip from the skill's page.</li>
<li>In ChatGPT, open <b>Skills → Create → Upload from your computer</b> and choose the .zip.</li></ol>
<h3>A plug-in (Claude only)</h3>
<ol><li>In Claude, go to <b>Customize → Plugins → + → Add marketplace</b>.</li>
<li>Enter <code>{REPO_SLUG}</code>.</li>
<li>Install the plug-in you want. Every skill inside it arrives at once, and it updates itself from then on.</li></ol>
<h3>An artifact</h3>
<ol><li>Download the artifact's <span class="mono">.html</span> file from its page.</li>
<li>In Claude Cowork, add the file to your session and ask Claude to <i>publish this file as an artifact</i>.</li>
<li>Claude gives you a link — open it, bookmark it, and use the tool from there.</li></ol>

<h2 id="using">Using a skill after you install it</h2>
<p><b>There is no command to type.</b> This surprises most people. Once a skill is installed, you just
describe what you want the way you normally would, and the assistant recognizes that the skill applies
and follows it.</p>
<p>For example, with the case generator installed, you'd simply write:</p>
<div class="ex"><span>“Write a case about Buc-ee's expansion strategy for my MBA operations class.”</span></div>
<p>Every skill's page in the catalog has a <b>“Try saying…”</b> section with a few real examples you can
copy and paste to see it work the first time.</p>

<h2 id="badges">What the badges mean</h2>
<p>Each item carries a badge saying where it works.</p>
<table><thead><tr><th>Badge</th><th>What it means for you</th></tr></thead><tbody>{badges}</tbody></table>

<h2 id="trouble">If something doesn't work</h2>
<h3>I installed it, but nothing seems to happen</h3>
<p>Skills activate when your request matches what they're for, so a very short or very general message may
not trigger one. Copy an example from the skill's “Try saying…” section — if that works, the skill is
installed correctly and it's just a matter of asking with a bit more detail. Also check you're in a
<i>new</i> conversation started after you installed it.</p>
<h3>Which file do I upload?</h3>
<p>The .zip file exactly as downloaded. Uploading a single file from inside it, or a folder you unzipped
yourself, won't work.</p>
<h3>How do I know when there's a newer version?</h3>
<p>Each catalog entry shows a version number and the date it was last updated. Plug-ins installed in Claude
update themselves; skills you uploaded by hand don't, so re-download and re-upload when the version changes.</p>
<h3>A skill says “Needs local software”</h3>
<p>It relies on programs that have to be installed on your own machine, so it can't run on the Claude or
ChatGPT websites. Its page explains what's required.</p>

<p style="margin-top:26px"><a class="back" href="index.html">← Back to the catalog</a></p>
<footer style="border:none">Have a skill of your own to share?
<a href="{REPO_URL}/blob/master/CONTRIBUTING.md">Submitting one takes about ten minutes</a> — no coding needed.</footer>
</main>
<script>{JS_HELP}</script>"""
    out = ROOT / "docs" / "start-here.html"
    out.write_text(page_shell("Start here", body, header))
    print(f"Wrote {out.relative_to(ROOT)}")


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


def main(strict=False):
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
    artifacts = load_artifacts()
    if artifacts:
        chips += f'<button class="chip" data-cat="Artifacts">Artifacts<span class="n">{len(artifacts)}</span></button>'
        grid += f'<h2 class="gsec" data-cat="Artifacts">Artifacts — interactive tools &middot; {len(artifacts)}</h2>'
        grid += "".join(artifact_card(a) for a in artifacts)
    n = len(report)
    total = n + len(artifacts)
    header = f"""<span style="float:right;font-size:14px"><a href="{REPO_URL}/blob/master/CONTRIBUTING.md">Contribute a skill (no coding needed)</a></span>
<h1>McCombs AI Skills</h1>
<p>Ready-made AI tools for teaching and learning at McCombs</p>"""
    body = f"""<div class="toolbar"><div class="wrap">
<div class="toolrow">
  <input id="q" type="search" placeholder="Search {total} skills &amp; artifacts — try “case”, “slides”, “prompt”…">
  <select id="sort" aria-label="Sort">
    <option value="cat" selected>By category</option>
    <option value="az">A–Z</option>
    <option value="new">Recently updated</option></select>
  <span class="count" id="count">{total} of {total}</span></div>
<div class="chips">{chips}</div>
</div></div>
<main class="wrap">
{help_strip()}
{bands}
<div class="grid" id="grid">{grid}<div class="empty" id="empty">No skills match — try a broader term.</div></div>
<footer>Maintained by the McCombs AI Faculty Working Group &middot; <a href="start-here.html">Start here guide</a>
&middot; <a href="option-c.html">Preview a new layout</a>
&middot; <a href="{REPO_URL}/blob/master/CONTRIBUTING.md">How to contribute or update a skill</a>
&middot; Skills follow the <a href="https://agentskills.io/specification">Agent Skills open standard</a>.</footer>
</main>
<script>{JS}</script>
<script>{JS_HELP}</script>"""
    out = ROOT / "docs" / "index.html"
    out.write_text(page_shell("Catalog", body, header))
    print(f"Wrote {out.relative_to(ROOT)} ({n} skills)")
    option_c_page(catalog_entries(report, artifacts))
    start_here_page()
    if markdown is None:
        print("WARNING: python 'markdown' package not installed — detail pages degraded to <pre> rendering.")
    if DATE_UNTRACKED:
        print(f"Note: no commits yet for {', '.join(DATE_UNTRACKED)} — showing today's date.")
    if DATE_ERRORS:
        print(f"WARNING: could not read the last-commit date for {len(DATE_ERRORS)} path(s); "
              "today's date was published instead, which is probably wrong:", file=sys.stderr)
        for err in DATE_ERRORS:
            print(f"  - {err}", file=sys.stderr)
        if strict:
            print("Failing because --strict was given. Re-run the build; this is usually transient.",
                  file=sys.stderr)
            return 1
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any per-skill 'updated' date had to be guessed")
    sys.exit(main(**vars(ap.parse_args())))
