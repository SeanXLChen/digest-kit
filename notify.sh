#!/bin/zsh
# Send the phone message to Telegram. Usage: notify.sh <title> <body>
# Reads TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID and optional TELEGRAM_THREAD_ID from
# ~/.config/digest-kit/telegram.env (outside git, chmod 600). No file = no-op, so the report still lands on disk.
# To use another channel (ntfy, Slack, email), replace this one file.

set -u

ENV="$HOME/.config/digest-kit/telegram.env"
[[ -f "$ENV" ]] || exit 0
source "$ENV"

title="$1" body="$2"

# Telegram limit is 4096 chars. Cut before escaping so no entity is split.
esc() { local s="${1//&/&amp;}"; s="${s//</&lt;}"; print -r -- "${s//>/&gt;}"; }
text="<b>$(esc "${title[1,150]}")</b>
$(esc "${body[1,3500]}")"

args=(-fsS -m 30 --retry 2 -F "chat_id=$TELEGRAM_CHAT_ID" -F "parse_mode=HTML")
[[ -n "${TELEGRAM_THREAD_ID:-}" ]] && args+=(-F "message_thread_id=$TELEGRAM_THREAD_ID")

# --form-string, not -F: -F reads a file when the value starts with "<" or "@".
curl "${args[@]}" --form-string "text=$text" \
  "https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage" >/dev/null
