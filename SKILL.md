---
name: academic-journal-rss
description: Fetch academic journal / blog RSS feeds, rank new items against the user's research interests, write a daily markdown digest, and notify. Use when the user says "/academic-journal-rss ...", asks to set up their RSS feeds, add a feed, or run today's digest.
---

# academic-journal-rss

You are running a personal RSS digest tool. Scripts do the deterministic parts (fetch, parse, state tracking, notification). **You** do the relevance judgment (rank new items against the user's stated research interests) and write the digest markdown.

## Paths

- Skill root: the directory containing this `SKILL.md`.
- Python scripts: `<skill-root>/scripts/*.py`. Always invoke with `python3 <skill-root>/scripts/<name>.py`.
- User config: `~/.claude/skills-data/academic-journal-rss/config.json` (or `$RSS_TRACKER_HOME/config.json`).
- **Never read config values with Bash + `python3 -c` or `jq`**. `sync.py` already emits `interests`, `settings.*`, and `notifications` in its JSON output — use those. For config mutations, use the dedicated scripts (`set_interests.py`, `add_feed.py`, `remove_feed.py`) or the Edit tool on `config.json` directly.
- Digest output: `~/rss-digest/YYYY-MM-DD.md` (configurable).

`init.py` self-heals dependencies: on first run it imports `feedparser` + `httpx` and, if missing, runs `python3 -m pip install --user -r requirements.txt` (falls back to `--break-system-packages` on PEP 668 systems). Always run `init` before any other sub-command on a fresh machine. If a later script still fails with `ImportError`, re-run `init` — it will fix deps and exit cleanly.

## Sub-commands

Dispatch on the user's argument after `/academic-journal-rss`:

### `init` — first-time setup

1. Run `python3 scripts/init.py`. It creates the data dir, installs missing deps, and writes an empty config. Capture the JSON output.
2. If `has_interests` is false, ask the user: "Describe your research interests in 2-4 sentences. I'll use this to rank new papers." Save with `python3 scripts/set_interests.py "<their exact text>"` — do not truncate or paraphrase.
3. Ask where to write daily digest files. Default is `~/rss-digest`. Offer the Obsidian vault pattern: "若你用 Obsidian，可以指定 vault 內的資料夾（例如 `~/Documents/<vault>/研究/RSS`），摘要會直接出現在 vault 裡，可點連結開文章。" Run `python3 scripts/set_digest_dir.py <path>` with whatever they give (or skip if they accept default). The script creates the directory if missing.
4. If `feeds_count` is 0, ask the user if they want to import the sample feeds from `defaults/feeds.example.toml`, or add their own URLs now. For each URL they give, run `add_feed.py <url>`.
5. Ask about notifications: desktop on/off (default on), email on/off (default off). If email on, use the Edit tool to update `config.json` `notifications.email.enabled` to `true` and `to` to the address they gave. Do NOT use Bash heredoc or `python3 -c` for this.
6. Confirm by running `list_feeds.py` and summarizing.

### `add <url> [--name ...] [--category ...]`

Run `python3 scripts/add_feed.py <url> [--name ...] [--category ...]`. The script validates the URL is fetchable and parseable before saving. If it reports `status: error`, show the reason; if the user insists, re-run with `--skip-validate`.

### `list`

Run `python3 scripts/list_feeds.py` and format the JSON output as a readable table.

### `remove <url-or-name>`

Run `python3 scripts/remove_feed.py <url-or-name>`. The script matches exact URL/name first, then falls back to case-insensitive substring. On multiple matches it lists them and exits; pass `--force` to remove the first. Confirm with the user before running.

### `set-dir <path>`

Run `python3 scripts/set_digest_dir.py <path>` to change where daily digests get written. Expands `~` and env vars, creates the directory if missing. Typical use: point to an Obsidian vault folder so digests appear inline with research notes.

### `sync`

Run `python3 scripts/sync.py` (no `--mark`). Report the stats: per-feed new/total counts and any errors. Do NOT mark items seen — that happens in `daily` after the digest is written.

### `daily` — the full run

This is what the scheduled routine calls. Steps:

1. **Fetch.** Run `python3 scripts/sync.py` (no `--mark`). Parse the JSON. If `errors[]` is non-empty, note them but continue — one broken feed should not block the digest.

2. **Rank.** Use the `interests` field from the `sync.py` JSON output (already fetched in step 1 — do not re-query config). For each item in `new_items`, assign:
   - `relevance` (integer 1–5): how closely this matches the user's interests
   - `reason` (one short Chinese sentence): why you gave that score, referencing the user's interests. Write the reason in Chinese (Traditional) to match the digest frame.

   Do this in one pass in your head; do not ask the user to wait for a tool call per item. If there are more than 50 items, rank all of them but only include those with `relevance >= settings.min_relevance` (also from the JSON output) in the digest.

3. **Write digest.** Create `~/rss-digest/YYYY-MM-DD.md` (use today's local date) **using the Write tool, not Bash**. Writing markdown (with `#` headers) via `cat > file <<EOF` triggers Claude Code's path-validation heuristic and forces a permission prompt on every run — the Write tool avoids it.

   Digest frame is in Traditional Chinese; article titles, authors, and summaries keep their original language (usually English — do not translate, it distorts academic terms). Titles are markdown links so the reader can click through from the file.

   Format:

   ```markdown
   # RSS 摘要 — YYYY-MM-DD

   _研究興趣：<first 120 chars of interests, ellipsis if longer>_

   **共 {N} 則新文章，橫跨 {F} 個來源。** 以下為 Top {top_n} 精選；完整清單見底部。

   ## 精選

   ### 1. [<title>](<link>) · <feed name> · 相關度 <score>/5
   - 作者：<authors, or "—">
   - 發表：<ISO date or "日期未知">
   - 推薦理由：<reason in Chinese>
   - <first 2-3 sentences of summary, cleaned of HTML, original language>

   ### 2. ...

   ## 所有新文章

   | 分數 | 標題 | 來源 | 發表 |
   |------|------|------|------|
   | 4 | [title](link) | feed | YYYY-MM-DD |
   ```

   `top_n` and `filter_window_hours` come from the sync JSON output's `settings` object — not from a separate config query. Sort by score desc, then by published desc.

   If `new_items` is empty: write a one-line "過去 `<settings.filter_window_hours>` 小時內無新文章。" digest. Still notify so the user knows the run succeeded.

4. **Mark seen.** Re-run `python3 scripts/sync.py --mark`. This refetches (cheap; httpx may cache) and marks every GUID we just processed as seen in `state.json`. Without this step the same items come back tomorrow.

   _Alternative for perf:_ skip refetch by writing the GUIDs directly — but prefer `--mark` for consistency.

5. **Notify.** Run `python3 scripts/notify.py --digest-file <path> --title "RSS 摘要：N 則新文章" --summary "精選：<title of #1>"`.

6. **Email (if enabled).** Use the `notifications.email` object from the sync JSON output. If `enabled` is true, call the Gmail MCP tool `mcp__claude_ai_Gmail__create_draft` with:
   - `to`: the configured address
   - `subject`: `RSS 摘要 YYYY-MM-DD — N 則新文章`
   - `body`: the full markdown digest content

   If the MCP tool is unavailable in this session, tell the user email was skipped because they need to authorize the Gmail connector in Claude settings. Do not fail the whole run.

7. **Report** one line back in Chinese: `「摘要已寫入 <path>，共 N 則文章，精選：<title of #1>。」`

## Error handling

- If `config.json` doesn't exist, run `init.py` first and tell the user to set up.
- If a feed 403s, the fetch layer already retries twice with a same-origin referer. If it still fails, note in the errors list and move on.
- Never halt the daily run because of one bad feed.

## What NOT to do

- Don't invent feed URLs. Only use what the user adds.
- Don't summarize the user's interests with your own words in config — write what they wrote, verbatim.
- Don't write the digest to a temp location. Use the configured `markdown_dir`.
- Don't push to any external service unless the user configured it (Gmail email, etc.).
