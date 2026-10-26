# digest-kit

A small local feed digest for macOS. It reads your RSS feeds, YouTube channels, GitHub Trending and Hacker News, asks Claude to pick what matters to you, saves a Markdown report, and sends a short message to your phone.

About 200 lines of zsh and Python. No server, no database, no dependencies beyond `python3`, `curl` and the [Claude Code](https://claude.com/claude-code) CLI.

## Why this and not a hosted digest

- **Runs on your Mac, not in an app.** launchd fires it hourly. If the Mac was asleep, it catches up on wake. You don't need any window open.
- **Items are marked seen only after the message is sent.** If the fetch, the model or the push fails, the next run retries the same items. Nothing is lost silently.
- **The model has no tools.** It runs with `--tools ""` and no MCP servers. A feed item that says "ignore previous instructions and run X" can only change the text of the digest, not do anything.
- **It ranks against your own notes.** You list a few Markdown files (what you work on, what you skip, what you already track). The model reads them on every run, so it drops things you already know about.

## Setup

```sh
git clone <this repo> ~/digest-kit && cd ~/digest-kit
cp config.example config                 # set OUTDIR and NOTES
cp sources.example.tsv sources.tsv       # your feeds
cp prompt.example.md prompt.md           # tune the picking rules and output format
FORCE=1 ./digest.sh                      # first run, ignores the schedule
```

The report lands in `$OUTDIR/YYYY-MM-DD.md`. Logs and the seen list are in `~/.local/state/digest-kit/<NAME>/`.

### Phone message (optional)

Create a Telegram bot with @BotFather, then:

```sh
mkdir -p ~/.config/digest-kit
cat > ~/.config/digest-kit/telegram.env <<'EOF'
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789
# TELEGRAM_THREAD_ID=42   # for a forum topic
EOF
chmod 600 ~/.config/digest-kit/telegram.env
```

Without this file, `notify.sh` does nothing and the report is still saved. To use ntfy, Slack or email instead, replace `notify.sh`.

### Schedule

Copy `launchd.example.plist` to `~/Library/LaunchAgents/`, fix the path, and load it (instructions are in the file). `EVERY` and `AFTER` in `config` decide how often it really runs.

To run several digests (say, one for AI and one for local news), make one config per digest with a different `NAME` and `OUTDIR`, and one plist per config passing the config path as the argument.

## Sources

`sources.tsv` is tab-separated: `kind  name  url`.

| kind | url column |
|---|---|
| `rss` | feed URL (RSS or Atom) |
| `youtube` | channel id (`UC...`) |
| `trending` | a GitHub Trending page URL |
| `hn` | `https://hn.algolia.com/api/v1/search` (stories over 150 points) |

One broken source is logged and skipped. The rest still run.

## Test

```sh
python3 test_fetch.py
```

Checks parsing, the seen filter, the age filter and the broken-source path, with no network.

## Cost

One `claude -p` call per run. Input is your notes plus the new items, usually a few thousand tokens. Use a smaller `MODEL` in `config` if you run it often.
