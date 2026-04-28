# Contributing to academic-journal-rss

Thanks for your interest. This is a small personal tool — contributions are welcome, but please open an Issue first so we can agree on the direction before you write code.

## Before you start

1. **Open an Issue** describing what you want to change and why.
2. Wait for a green light. Small bug fixes can skip this; new features and behaviour changes cannot.
3. Fork the repo, make your changes, then open a Pull Request against `main`.

## Local setup

```bash
git clone https://github.com/chinhsi/academic-journal-rss.git
cd academic-journal-rss
pip install -r requirements.txt
```

Test manually with a real feed URL:

```bash
python3 scripts/add_feed.py https://arxiv.org/rss/cs.AI --name "arXiv CS.AI"
python3 scripts/sync.py
```

No automated test suite yet — manual smoke-test is sufficient for now.

## Where contributions are most useful

| Area | What to send |
|---|---|
| **Publisher feed fixes** | A working URL + any custom headers needed for a blocked publisher (Wiley, Springer, ASCO, etc.) — add an entry to `defaults/feeds.example.toml` |
| **Bug reports** | The feed URL, the error message from `sync.py`, and your OS / Python version |
| **Cloudflare / 403 bypasses** | A PR against `lib/fetcher.py` with a minimal, tested fix |
| **New scripts** | Keep the same `--output JSON` contract as `sync.py` so the Claude skill can consume it |
| **README / docs** | Always welcome |

## Things to avoid

- Don't add new required dependencies without discussion — the install path must stay as simple as `pip install -r requirements.txt`.
- Don't break the `--output JSON` contract of any existing script — the Claude skill depends on this.
- Don't add calls to external APIs or services that require account sign-up.

## Pull Request checklist

- [ ] Tested locally against at least one real feed
- [ ] `requirements.txt` updated if you added a dependency
- [ ] `README.md` updated if you added a user-facing feature

## Code style

Plain Python 3.9+. No formatter enforced, but follow the style of surrounding code — 4-space indent, no type annotations required.

## License

By contributing you agree that your code will be released under the [MIT License](LICENSE).
