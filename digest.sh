#!/bin/zsh
# Local feed digest: fetch sources -> one model call with no tools -> Markdown report + phone message.
# Usage: digest.sh [config]   (default: ./config next to this script; FORCE=1 skips the schedule check)
# Driven by launchd (see launchd.example.plist). macOS only: uses BSD `date -j`.

set -u

export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

DIR="${0:A:h}"
CONFIG="${1:-$DIR/config}"
[[ -f "$CONFIG" ]] || { print -u2 "digest.sh: no config at $CONFIG (copy config.example)"; exit 2; }
# Defaults; config overrides any of them.
NAME=digest
SOURCES="$DIR/sources.tsv"
PROMPT="$DIR/prompt.md"
NOTES=()
OUTDIR="$HOME/digests"
EVERY=1
AFTER=0800
MODEL=claude-opus-5
source "$CONFIG"

STATE="$HOME/.local/state/digest-kit/$NAME"
LOG="$STATE/run.log"
TODAY="$(date +%F)"

mkdir -p "$OUTDIR" "$STATE"
[[ -f "$STATE/seen.json" ]] || print '[]' > "$STATE/seen.json"
say() { print -r -- "[$(date '+%F %T')] $*" >> "$LOG"; }
notify() { "$DIR/notify.sh" "$@" 2>>"$LOG" || say "WARN: notify failed"; }

# StartInterval fires hourly so a sleeping Mac still runs on wake; the checks make it once every $EVERY days.
LAST=$(ls "$OUTDIR" 2>/dev/null | grep -E '^[0-9]{4}-[0-9]{2}-[0-9]{2}\.md$' | tail -1)
DAYS=$EVERY
[[ -n "$LAST" ]] && DAYS=$(( ( $(date -j -f %F "$TODAY" +%s) - $(date -j -f %F "${LAST%.md}" +%s) ) / 86400 ))
if [[ "${FORCE:-0}" != "1" ]]; then
  [[ "$(date +%H%M)" < "$AFTER" ]] && exit 0
  (( DAYS < EVERY )) && exit 0
fi

say "start $TODAY (last: ${LAST:-none})"
TMP=$(mktemp -d); trap 'rm -rf "$TMP"' EXIT

if ! python3 "$DIR/fetch.py" "$SOURCES" "$STATE/seen.json" "$(( DAYS > 0 ? DAYS : EVERY ))" > "$TMP/items.json" 2>>"$LOG"; then
  say "abort: fetch failed"; notify "$NAME failed" "Fetch failed, see $LOG"; exit 1
fi
python3 -c 'import json,sys; d=json.load(open(sys.argv[1])); print(len(d["items"]), "items; errors:", d["errors"])' "$TMP/items.json" | while read -r l; do say "fetched $l"; done

{
  cat "$PROMPT"
  print "\n---\n## Input\n\nDate: $TODAY\n"
  for n in "${NOTES[@]}"; do print "\n### ${n:t:r}\n"; cat "$n"; done
  print "\n### New items (JSON)\n"; cat "$TMP/items.json"
} > "$TMP/prompt.md"

# No tools and no MCP: the model only reads the input and prints. Feed items are untrusted text.
OUT=$(ENABLE_CLAUDEAI_MCP_SERVERS=false claude -p --model "$MODEL" --strict-mcp-config --tools "" < "$TMP/prompt.md" 2>>"$LOG")
STATUS=$?
if [[ $STATUS -ne 0 || "$OUT" != *"===PHONE==="* ]]; then
  say "FAIL exit=$STATUS (no delimiter or error)"; notify "$NAME failed" "Bad model output, see $LOG"; exit 1
fi

# The model sometimes wraps Part 1 in a ``` fence copied from the prompt template.
print -r -- "${OUT%%===PHONE===*}" | sed '/^```[a-z]*$/d' > "$OUTDIR/$TODAY.md"
PHONE="${OUT#*===PHONE===}"; PHONE="${PHONE#$'\n'}"
notify "$NAME · $TODAY" "$PHONE"

# Only now mark as seen, so a failed run retries the same items next time.
python3 - "$STATE/seen.json" "$TMP/items.json" <<'PY'
import json, sys
seen = set(json.load(open(sys.argv[1])))
seen |= {i["url"] for i in json.load(open(sys.argv[2]))["items"]}
json.dump(sorted(seen), open(sys.argv[1], "w"))
PY
say "done"
