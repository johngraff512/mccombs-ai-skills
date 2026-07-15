# Contributing a skill (no coding experience needed)

Thanks for sharing a skill with your McCombs colleagues! There are two ways to submit. Most faculty should use **Path A** — it happens entirely in your web browser, no software to install.

## What you're submitting

A skill is just a **folder** containing a file named `SKILL.md` (a plain-text instruction file), plus any supporting files (templates, reference documents). If you built your skill in Claude or ChatGPT, you already have this folder — it's what you would upload to either platform.

Not sure your folder is set up right? Ask Claude or ChatGPT: *"Check that this folder follows the Agent Skills specification at agentskills.io"* — or just submit it and our automatic checker will tell you exactly what to fix.

## Path A: Submit through the GitHub website (recommended)

**One-time preparation:** create a free account at [github.com/signup](https://github.com/signup) (any email works; takes 2 minutes).

1. Go to the repository: **github.com/johngraff512/mccombs-ai-skills** and make sure you're signed in (your picture appears top-right).
2. Click the **`plugins`** folder, then the plugin your skill belongs in (use **`community-skills`** if unsure), then its **`skills`** folder. You should now see the existing skill folders.
3. Click the **"Add file"** button (near the top right of the file list), then **"Upload files"**.
4. **Drag your entire skill folder** from your computer (Finder or File Explorer) into the upload area on the page. Important: drag the *folder itself*, not a zip file — GitHub keeps the folder structure automatically. You'll see your files listed with names like `your-skill-name/SKILL.md`.
5. Scroll down to the **"Propose changes"** box:
   - In the first (short) text field, type something like: `Add negotiation-roleplay skill`
   - In the larger field, briefly say what the skill does and whether you tested it in Claude, ChatGPT, or both.
6. Click the green **"Propose changes"** button, then on the next page click **"Create pull request"** (twice if asked). A "pull request" is GitHub's version of a suggestion box — nothing goes live until a working-group member approves it.

**What happens next (automatically):**

- Within a minute or two, our robot checker validates your skill and labels it *Both platforms*, *Both (see notes)*, or *Claude only*. If something needs fixing, it leaves a plain-English note on your pull request (you'll get an email).
- A working-group member reviews and approves it. Your skill then appears on the [skill catalog](https://johngraff512.github.io/mccombs-ai-skills/) for all faculty, with you credited as author.

## Path B: Submit with Git (for the comfortable)

1. Fork/branch, add your skill folder under `plugins/<plugin>/skills/<skill-name>/` (must contain `SKILL.md`; see the [spec](https://agentskills.io/specification)).
2. Run the checks locally before pushing:

```bash
pip install pyyaml
python3 scripts/check_skills.py                 # validation + compatibility report
python3 scripts/package_skills.py               # build zips into dist/
python3 scripts/check_skills.py --json docs/compat-report.json && python3 scripts/build_catalog.py
open docs/index.html                            # preview the catalog
```

3. Open a pull request — the template walks you through the checklist, including a manual test on both platforms.

## Can't or don't want to use GitHub at all?

Email your skill folder (zipped) to the AI Faculty Working Group and we'll submit it for you, credited to you.

## Ground rules for all submissions

- No student data (FERPA), no secrets or API keys, no copyrighted third-party material you don't have rights to share.
- If your skill adapts someone else's work, credit them in the SKILL.md and include their license.
- Test your skill with at least one realistic prompt before submitting — on both platforms if you can.
