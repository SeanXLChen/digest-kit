<p align="center"><img src="assets/banner.png" alt="digest-kit: your Mac mini reads the internet for you" width="100%"></p>

<p align="center"><b>English</b> · <a href="README.zh-CN.md">简体中文</a></p>

<p align="center">
  <img src="https://img.shields.io/badge/macOS-launchd-black?logo=apple" alt="macOS launchd">
  <img src="https://img.shields.io/badge/runs%20on-Claude%20Code-d97757" alt="Claude Code">
  <img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT">
</p>

# digest-kit

**Your Mac mini is on 24/7 anyway. Let it read your feeds every morning and send you the few things worth your time.**

digest-kit fetches your RSS feeds, YouTube channels, GitHub Trending and Hacker News, asks Claude to pick what matters *to you*, saves a Markdown report, and pings your phone on Telegram.

About 200 lines of zsh and Python. No server, no database, no Docker. Just `python3`, `curl` and the [Claude Code](https://claude.com/claude-code) CLI you already have.

## 👀 What you get

A real run, unedited, with the example sources and a two-line interests file:

```markdown
## Try
1. **Graphify** https://github.com/Graphify-Labs/graphify — Turn any codebase into a queryable
   knowledge graph for Claude Code using local deterministic AST parsing.
   Why it fits: Local-first approach, direct Claude Code skill integration.
...
## Read
No strong picks this week. HN content was mostly off-topic (politics, health news, general essays).

## Dropped
20 items. Reasons: off-topic, outside stated interests, insufficient summary detail.
```

It says "nothing good today" when there is nothing good. That's the point.

## 🖥️ Made for the Mac that never sleeps

If you keep a Mac mini (or any always-on Mac) running agents, this slots right in:

- **launchd, not an app.** It fires hourly and decides itself whether today is a run day. A Mac that was asleep catches up on wake. No window, no menu-bar icon.
- **Nothing gets lost.** Items are marked seen only *after* the phone message is sent. If the fetch, the model or Telegram fails, the next run retries the same items.
- **Safe to run unattended.** The model runs with no tools (`--tools ""`, no MCP servers). A feed item that says "ignore previous instructions and run X" can only change the text of the digest. It can't touch your machine.
- **Ranks against your own notes.** Point it at a few Markdown files (what you work on, what you skip, what you already follow). It drops what you already know about.

## 🚀 Setup (5 minutes)

```sh
git clone https://github.com/SeanXLChen/digest-kit ~/digest-kit && cd ~/digest-kit
cp config.example config                 # set OUTDIR and NOTES
cp sources.example.tsv sources.tsv       # your feeds
cp prompt.example.md prompt.md           # picking rules and output format
FORCE=1 ./digest.sh                      # first run, ignores the schedule
```

The report lands in `$OUTDIR/YYYY-MM-DD.md`. Logs and the seen list live in `~/.local/state/digest-kit/<NAME>/`.

### 📱 Phone message (optional)

Create a Telegram bot with [@BotFather](https://t.me/BotFather), then:

```sh
mkdir -p ~/.config/digest-kit
cat > ~/.config/digest-kit/telegram.env <<'EOF'
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_CHAT_ID=123456789
# TELEGRAM_THREAD_ID=42   # for a forum topic
EOF
chmod 600 ~/.config/digest-kit/telegram.env
```

No file, no message; the report is still saved. Prefer ntfy, Slack or email? Replace `notify.sh`, it's 25 lines.

### ⏰ Schedule

```sh
sed "s|/PATH/TO|$HOME|" launchd.example.plist > ~/Library/LaunchAgents/local.digest-kit.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/local.digest-kit.plist
```

`EVERY` (days) and `AFTER` (HHMM) in `config` decide how often it really runs.

**Several digests** (say, AI news and local news): one config per digest with its own `NAME` and `OUTDIR`, and one plist per config passing the config path as the argument.

## 📡 Sources

`sources.tsv` is tab-separated: `kind  name  url`.

| kind | url column |
|---|---|
| `rss` | feed URL (RSS or Atom) |
| `youtube` | channel id (`UC...`) |
| `trending` | a GitHub Trending page URL |
| `hn` | `https://hn.algolia.com/api/v1/search` (stories over 150 points) |

One broken source is logged and skipped. The rest still run.

## 🧪 Test

```sh
python3 test_fetch.py
```

Checks parsing, the seen filter, the age filter and the broken-source path, with no network.

## 💸 Cost

One `claude -p` call per run. Input is your notes plus the new items, usually a few thousand tokens. Running daily? Set a smaller `MODEL` in `config`.

## 📜 License

[MIT](LICENSE)
