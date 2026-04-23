---
name: academic-journal-rss
description: Fetch academic journal / blog RSS feeds, rank new items against the user's research interests, write a daily markdown digest, and notify. Use when the user says "/academic-journal-rss ...", asks to set up their RSS feeds, add a feed, or run today's digest.
---

# academic-journal-rss

You are running a personal RSS digest tool. Scripts do the deterministic parts (fetch, parse, state tracking, notification). **You** do the relevance judgment (rank new items against the user's stated research interests) and write the digest markdown.

## Paths

- Skill root: the directory containing this `SKILL.md`.
- Python scripts: `<skill-root>/scripts/*.py`. Always invoke with `python3 <skill-root>/scripts/<name>.py`.
- User config: `~/.claude/skills-data/rss-tracker/config.json` (or `$RSS_TRACKER_HOME/config.json`).
- Digest output: `~/rss-digest/YYYY-MM-DD.md` (configurable).

`init.py` self-heals dependencies: on first run it imports `feedparser` + `httpx` and, if missing, runs `python3 -m pip install --user -r requirements.txt` (falls back to `--break-system-packages` on PEP 668 systems). Always run `init` before any other sub-command on a fresh machine. If a later script still fails with `ImportError`, re-run `init` — it will fix deps and exit cleanly.

## Sub-commands

Dispatch on the user's argument after `/academic-journal-rss`:

### `init` — first-time setup

1. Run `python3 scripts/init.py`. It creates the data dir, installs missing deps, and writes an empty config. Capture the JSON output.
2. If `has_interests` is false, ask the user: "Describe your research interests in 2-4 sentences. I'll use this to rank new papers." Save with `python3 scripts/set_interests.py "<their exact text>"` — do not truncate or paraphrase.
3. If `feeds_count` is 0, ask the user if they want to import the sample feeds from `defaults/feeds.example.toml`, or add their own URLs now. For each URL they give, run `add_feed.py <url>`.
4. Ask about notifications: desktop on/off (default on), email on/off (default off). If email on, use the Edit tool to update `config.json` `notifications.email.enabled` to `true` and `to` to the address they gave. Do NOT use Bash heredoc or `python3 -c` for this.
5. Confirm by running `list_feeds.py` and summarizing.

### `add <url> [--name ...] [--category ...]`

Run `python3 scripts/add_feed.py <url> [--name ...] [--category ...]`. The script validates the URL is fetchable and parseable before saving. If it reports `status: error`, show the reason; if the user insists, re-run with `--skip-validate`.

### `list`

Run `python3 scripts/list_feeds.py` and format the JSON output as a readable table.

### `remove <url-or-name>`

Run `python3 scripts/remove_feed.py <url-or-name>`. The script matches exact URL/name first, then falls back to case-insensitive substring. On multiple matches it lists them and exits; pass `--force` to remove the first. Confirm with the user before running.

### `sync`

Run `python3 scripts/sync.py` (no `--mark`). Report the stats: per-feed new/total counts and any errors. Do NOT mark items seen — that happens in `daily` after the digest is written.

### `daily` — the full run

This is what the scheduled routine calls. Steps:

1. **Fetch.** Run `python3 scripts/sync.py` (no `--mark`). Parse the JSON. If `errors[]` is non-empty, note them but continue — one broken feed should not block the digest.

2. **Rank.** Load `config.json` → `interests`. For each item in `new_items`, assign:
   - `relevance` (integer 1–5): how closely this matches the user's interests
   - `reason` (one short sentence): why you gave that score, referencing the user's interests

   Do this in one pass in your head; do not ask the user to wait for a tool call per item. If there are more than 50 items, rank all of them but only include those with `relevance >= settings.min_relevance` in the digest.

3. **Write digest.** Create `~/rss-digest/YYYY-MM-DD.md` (use today's local date) **using the Write tool, not Bash**. Writing markdown (with `#` headers) via `cat > file <<EOF` triggers Claude Code's path-validation heuristic and forces a permission prompt on every run — the Write tool avoids it. Format:

   ```markdown
   # RSS digest — YYYY-MM-DD

   _Interests: <first 120 chars of interests, ellipsis if longer>_

   **{N} new items ranked across {F} feeds.** Top {top_n} below; full list at the bottom.

   ## Top picks

   ### 1. <title> · <feed name> · relevance <score>/5
   - <link>
   - Authors: <authors, or "—">
   - Published: <ISO date or "unknown">
   - Why: <reason>
   - <first 2-3 sentences of summary, cleaned of HTML>

   ### 2. ...

   ## All new items

   | Score | Title | Feed | Link |
   |-------|-------|------|------|
   | 4 | ... | ... | ... |
   ```

   Top {top_n} = `settings.top_n` from config (default 5). Sort by score desc, then by published desc.

   If `new_items` is empty: write a one-line "No new items in the last {window_hours}h." digest. Still notify so the user knows the run succeeded.

4. **Mark seen.** Re-run `python3 scripts/sync.py --mark`. This refetches (cheap; httpx may cache) and marks every GUID we just processed as seen in `state.json`. Without this step the same items come back tomorrow.

   _Alternative for perf:_ skip refetch by writing the GUIDs directly — but prefer `--mark` for consistency.

5. **Notify.** Run `python3 scripts/notify.py --digest-file <path> --title "RSS digest: N new items" --summary "Top: <title of #1>"`.

6. **Email (if enabled).** Read `config.json` → `notifications.email`. If `enabled` is true, call the Gmail MCP tool `mcp__claude_ai_Gmail__create_draft` with:
   - `to`: the configured address
   - `subject`: `RSS digest YYYY-MM-DD — N new`
   - `body`: the full markdown digest content

   If the MCP tool is unavailable in this session, tell the user email was skipped because they need to authorize the Gmail connector in Claude settings. Do not fail the whole run.

7. **Report** one line back: `"Digest written to <path>. N items ranked. Top: <title of #1>."`

## Error handling

- If `config.json` doesn't exist, run `init.py` first and tell the user to set up.
- If a feed 403s, the fetch layer already retries twice with a same-origin referer. If it still fails, note in the errors list and move on.
- Never halt the daily run because of one bad feed.

## What NOT to do

- Don't invent feed URLs. Only use what the user adds.
- Don't summarize the user's interests with your own words in config — write what they wrote, verbatim.
- Don't write the digest to a temp location. Use the configured `markdown_dir`.
- Don't push to any external service unless the user configured it (Gmail email, etc.).
