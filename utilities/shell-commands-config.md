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

### Command 1 — Regenerate HTML Preview (file-save trigger)

**Alias:** `Regenerate HTML Preview`

**Command:**
```bash
python "{{vault_path}}/utilities/legendkeeper-pipeline/generate_world_html.py" --source "{{file_path:absolute}}" --open
```

**Behavior:**
- Runs whenever you save a pipeline source file (`type: myth|lore|timeline`)
- Generates `docs/<slug>.html` locally (no `--public` flag — full GM preview)
- Opens the generated HTML in your default browser
- Non-pipeline files (location notes, faction docs, etc.) **exit silently** — no output, no error
- GM-only files (`visibility: gm_secrets`) generate locally — you can preview all content

**Configure Events tab:**
1. Under the command's **Events** tab → enable **"After saving a file"**
2. Under **Folder restrictions** → restrict to `world` and `narrative` (prevents triggering on unrelated saves)

**Configure Output tab:**
- stdout → **Status bar** (brief success message)
- stderr → **Notification** (shows errors prominently)

---

### Command 2 — Full Pipeline (Local)

**Alias:** `Full Pipeline (Local)`

**Command (macOS/Linux):**
```bash
cd "{{vault_path}}" && python utilities/dashboard/generate_dashboard.py --out docs/dashboard.html && python utilities/campaign_frame/generate_campaign_frame.py --out docs/campaign-frame.html && python utilities/legendkeeper-pipeline/generate_all_world_html.py && open docs/index.html
```

**Behavior:**
- Runs all three generators: dashboard, campaign frame, world HTML + index
- No `--public` flag — generates everything including GM-only docs for full local review
- Opens `docs/index.html` in browser when complete

**Configure Hotkey:** Assign `Cmd+Shift+B` (or your preference) via Settings → Hotkeys → search "Full Pipeline".

**Configure Output tab:**
- stdout → **Notification** ("Pipeline complete" summary)
- stderr → **Notification**

---

### Command 3 — Open Local Preview (optional convenience)

**Alias:** `Open Local Preview`

**Command:**
```bash
open "{{vault_path}}/docs/{{file_name:stem}}.html"
```

**Behavior:**
- Opens the already-generated HTML for the current file — does NOT regenerate
- Use when you've already run Command 1 and just want to re-open the browser tab
- Works reliably for kebab-case filenames (all existing world docs); may not resolve correctly for files with spaces or special characters

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
- Verify the "After saving a file" event is enabled on the command
- Check folder restrictions — ensure `world` and `narrative` are included
- Confirm the file has `type: myth`, `type: lore`, or `type: timeline` in frontmatter

**"HTML not found" when opening preview:**
- Run Command 1 manually first to generate the file
- Check `docs/` directory exists in vault root

**Python not found:**
- Ensure Python 3 is in your PATH: `which python3` in terminal
- If needed, use full path: `/usr/bin/python3` or `/usr/local/bin/python3`
- On macOS with Homebrew: `/opt/homebrew/bin/python3`

**pyyaml not installed:**
```bash
pip install pyyaml
```
Without pyyaml, the generator falls back to a basic frontmatter parser — most cases work, but YAML lists and quoted values may parse differently.
