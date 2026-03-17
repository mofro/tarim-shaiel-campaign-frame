---
title: Obsidian Shell Commands — Pipeline Setup
project: TTRPG_Tarim_Shaiel
type: operational
visibility: public
status: active
created: 2026-03-17
last_updated: 2026-03-17
---

# Obsidian Shell Commands — Pipeline Setup

Configures the [Shell Commands](https://github.com/Tero-Laitinen/obsidian-shellcommands) community plugin to trigger the HTML generation pipeline from within Obsidian.

**Install first:** Settings → Community plugins → Browse → search "Shell Commands" → Install → Enable.

---

## Commands to Configure

Open Settings → Shell Commands → click **"+"** to add each command.

---

### Command 1 — Regenerate HTML Preview (manual)

**Alias:** `Regenerate HTML Preview`

**Command:**
```bash
/opt/homebrew/bin/python3 /Users/mo/Documents/Games/HeroHeaven/utilities/legendkeeper-pipeline/generate_world_html.py {{file_path:absolute}}
```

**Behavior:**
- Run manually from the palette when you want to regenerate a single pipeline file
- Only processes files with `type: myth`, `type: lore`, or `type: timeline` — exits silently for everything else
- No `--public` flag — generates locally including GM-only content
- Use Command 3 (Open Local Preview) to view the result after running

**No event trigger** — on-save auto-trigger was disabled (autosave loop; Command 2 hotkey is sufficient)

**Configure Output tab:**
- stdout → **Status bar** (brief success message)
- stderr → **Error balloon** (shows errors prominently)

---

### Command 2 — Full Pipeline (Local)

**Alias:** `Full Pipeline (Local)`

**Command (macOS/Linux):**
```bash
/opt/homebrew/bin/python3 /Users/mo/Documents/Games/HeroHeaven/utilities/dashboard/generate_dashboard.py --out /Users/mo/Documents/Games/HeroHeaven/docs/dashboard.html && /opt/homebrew/bin/python3 /Users/mo/Documents/Games/HeroHeaven/utilities/campaign_frame/generate_campaign_frame.py --out /Users/mo/Documents/Games/HeroHeaven/docs/campaign-frame.html && /opt/homebrew/bin/python3 /Users/mo/Documents/Games/HeroHeaven/utilities/legendkeeper-pipeline/generate_all_world_html.py && open /Users/mo/Documents/Games/HeroHeaven/docs/index.html
```

_Note: `{{vault_path}}` expands with escaped backslashes and doubles the path — hardcoded path is intentional._

**Behavior:**
- Runs all three generators: dashboard, campaign frame, world HTML + index
- No `--public` flag — generates everything including GM-only docs for full local review
- Opens `docs/index.html` in browser when complete

**Configure Hotkey:** Assign `Cmd+Shift+B` (or your preference) via Settings → Hotkeys → search "Full Pipeline".

**Configure Output tab:**
- stdout → **Error balloon** (shows completion summary)
- stderr → **Error balloon**

---

### Command 3 — Open Local Preview (optional convenience)

**Alias:** `Open Local Preview`

**Command:**
```bash
open /Users/mo/Documents/Games/HeroHeaven/docs/$(basename "{{file_path:absolute}}" .md).html
```

**Behavior:**
- Opens the already-generated HTML for the current file — does NOT regenerate
- Use when you've already run Command 1 and just want to re-open the browser tab
- Uses `basename` to strip `.md` extension — more reliable than plugin filename variables

---

## Variable Reference

These are Shell Commands plugin variables used above:

| Variable | Value |
|----------|-------|
| `{{vault_path}}` | Absolute path to the Obsidian vault root (no trailing slash) |
| `{{file_path:absolute}}` | Absolute path to the currently open file |
| `{{file_name:stem}}` | Filename without extension (e.g. `nianhao-the-divine-arc`) |

---

## Visibility Gating Reminder

Commands 1 and 2 run **without** `--public` — they generate ALL documents including `visibility: gm_secrets` files. This is intentional for local GM preview.

The `--public` flag is only used by:
- `netlify.toml` (Netlify deploys)
- `.github/workflows/generate-html.yml` (GitHub Actions commits to `docs/`)

**Never add `--public` to Shell Commands.** Local = full preview. Remote = public only.

---

## Troubleshooting

**Command doesn't trigger on save:**
- Verify the "File content modified" event is enabled on the command
- Check folder restrictions — ensure `world` and `narrative` are included
- Confirm the file has `type: myth`, `type: lore`, or `type: timeline` in frontmatter

**"HTML not found" when opening preview:**
- Run Command 1 manually first to generate the file
- Check `docs/` directory exists in vault root

**Wrong Python version (Xcode Python 3.9 instead of Homebrew 3.13):**
- Shell Commands plugin may pick up `/Applications/Xcode.app/.../python3` (3.9) instead of Homebrew
- Fix: use full Homebrew path in commands: `/opt/homebrew/bin/python3`
- Verify: `which python3` and `python3 --version` in terminal — should show 3.10+

**pyyaml not installed:**
```bash
pip install pyyaml
```
Without pyyaml, the generator falls back to a basic frontmatter parser — most cases work, but YAML lists and quoted values may parse differently.
