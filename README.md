# academic-journal-rss

A Claude Code skill that fetches journal / blog RSS feeds daily, ranks new items against your research interests, and drops a markdown digest you can open in any editor.

Built for graduate students. No Discord server, no Telegram bot, no API keys required.

## What it does

1. You configure a list of RSS feeds and a short paragraph describing your research interests.
2. Once a day (via Claude's scheduler, or manually), the skill fetches every feed, picks new items, ranks them against your interests, and writes `~/rss-digest/YYYY-MM-DD.md`.
3. Optional: desktop notification, or email-to-self via the Claude.ai Gmail connector.

Cloudflare-protected publishers (ASCO, NEJM, OUP, Wiley, Nature, Taylor & Francis…) are handled with browser-mimicking headers — no extra setup.

## Install

```bash
git clone https://github.com/chinhsi/academic-journal-rss.git ~/.claude/skills/academic-journal-rss
cd ~/.claude/skills/academic-journal-rss
pip install -r requirements.txt
```

Then in Claude Code:

```
/academic-journal-rss init
```

This sets up `~/.claude/skills-data/academic-journal-rss/` with your `config.json` and walks you through adding your first feeds + interest statement.

## Daily use

```
/academic-journal-rss daily
```

Runs: sync → filter new items → rank against interests → write markdown digest → notify.

Schedule it:

```
/schedule daily 07:00 /academic-journal-rss daily
```

## Commands

| Command | What |
|---|---|
| `/academic-journal-rss init` | First-time setup |
| `/academic-journal-rss add <url> [--name ...] [--category ...]` | Add a feed |
| `/academic-journal-rss list` | Show all feeds |
| `/academic-journal-rss sync` | Fetch feeds, detect new items (no digest) |
| `/academic-journal-rss daily` | Full run: sync + digest + notify |

## Where your data lives

```
~/.claude/skills-data/academic-journal-rss/
├── config.json    # feeds, interests, notification prefs
└── state.json     # seen GUIDs + last run timestamps
~/rss-digest/
└── 2026-04-23.md  # daily markdown digests
```

Everything is plain text. Delete to reset.

Override locations with env vars:

```bash
export RSS_TRACKER_HOME=~/my-rss-data
export RSS_TRACKER_DIGEST_DIR=~/Documents/rss
```

## How it handles different publishers

- **Parsing**: `feedparser` handles RSS 1.0/2.0/Atom and most malformed feeds.
- **Fetching**: `httpx` session with realistic Chrome `User-Agent`, `Accept`, `Accept-Language`, same-origin `Referer`, cookie jar, and 403 retry with backoff. This defeats the Cloudflare/Atypon challenge that blocks bare Python clients on academic publisher sites.

If a particular feed still fails, add it to `feed_overrides` in `config.json` with custom headers or a specific `Referer`:

```json
{
  "feed_overrides": {
    "https://problem-publisher.com/rss": {
      "headers": {"User-Agent": "..."},
      "referer": "https://problem-publisher.com/journal/home"
    }
  }
}
```

## Optional: faster HTTP/2

Some Cloudflare edges prefer HTTP/2. Install the optional dep:

```bash
pip install 'httpx[http2]'
```

The skill auto-detects `h2` at runtime; no code change needed.

## Sample feeds

See [`defaults/feeds.example.toml`](defaults/feeds.example.toml) for sample URLs across CS, medicine, and education. Add any with:

```
/academic-journal-rss add <url>
```

## License

MIT
