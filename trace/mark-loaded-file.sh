#!/usr/bin/env bash
# Mark a file as actually loaded/read for the current Runtime Trace session.
# This does not prove model comprehension; it records a verifiable file path,
# file hash, and Rule IDs for later Spec Evidence validation.
#
# Usage:
#   .harness/trace/mark-loaded-file.sh --path docs/TRD.md
#   .harness/trace/mark-loaded-file.sh --trace-id trace-... --path commands/run.md

set -euo pipefail

TRACE_ID=""
PATH_VALUE=""

while [ $# -gt 0 ]; do
  case "$1" in
    --trace-id) TRACE_ID="$2"; shift 2 ;;
    --path|--file) PATH_VALUE="$2"; shift 2 ;;
    *) shift ;;
  esac
done

if [ -z "$PATH_VALUE" ]; then
  echo "Usage: $0 --path <file> [--trace-id <trace_id>]" >&2
  exit 1
fi

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
TRACE_DIR="$ROOT/.harness/trace"
LATEST="$TRACE_DIR/latest-runtime-trace.json"

if [ -z "$TRACE_ID" ]; then
  if [ ! -f "$LATEST" ]; then
    echo "No latest runtime trace found. Run record-runtime-trace.sh first." >&2
    exit 1
  fi
  TRACE_ID="$(sed -n 's/.*"trace_id":"\([^"]*\)".*/\1/p' "$LATEST" | head -n 1)"
fi

if [ -z "$TRACE_ID" ]; then
  echo "Unable to resolve trace_id." >&2
  exit 1
fi

case "$PATH_VALUE" in
  /*) FULL_PATH="$PATH_VALUE"; REL_PATH="${PATH_VALUE#$ROOT/}" ;;
  *) FULL_PATH="$ROOT/$PATH_VALUE"; REL_PATH="$PATH_VALUE" ;;
esac

if [ ! -f "$FULL_PATH" ]; then
  echo "File not found: $REL_PATH" >&2
  exit 1
fi

SESSION_DIR="$TRACE_DIR/sessions/$TRACE_ID"
mkdir -p "$SESSION_DIR"

timestamp() {
  date -u +"%Y-%m-%dT%H:%M:%SZ"
}

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g; s/	/\\t/g'
}

json_array() {
  local first=1
  printf '['
  for item in "$@"; do
    [ -n "$item" ] || continue
    if [ "$first" -eq 0 ]; then printf ','; fi
    printf '"%s"' "$(json_escape "$item")"
    first=0
  done
  printf ']'
}

SHA256="$(shasum -a 256 "$FULL_PATH" | awk '{print $1}')"
SIZE_BYTES="$(wc -c < "$FULL_PATH" | tr -d ' ')"
MTIME="$(date -u -r "$FULL_PATH" +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -u +"%Y-%m-%dT%H:%M:%SZ")"

RULE_IDS=()
ids="$(grep -Eo 'RULE-[A-Z0-9-]+-[0-9]+' "$FULL_PATH" 2>/dev/null | sort -u || true)"
if [ -n "$ids" ]; then
  while IFS= read -r id; do
    [ -n "$id" ] && RULE_IDS+=("$id")
  done <<EOF_IDS
$ids
EOF_IDS
fi

record=$(printf '{"timestamp":"%s","trace_id":"%s","path":"%s","sha256":"%s","size_bytes":%s,"mtime":"%s","rule_ids":%s,"loaded_by":"mark-loaded-file"}' \
  "$(timestamp)" \
  "$(json_escape "$TRACE_ID")" \
  "$(json_escape "$REL_PATH")" \
  "$(json_escape "$SHA256")" \
  "$SIZE_BYTES" \
  "$(json_escape "$MTIME")" \
  "$(json_array "${RULE_IDS[@]}")")

printf '%s\n' "$record" >> "$SESSION_DIR/loaded-files.jsonl"
printf '%s\n' "$record" >> "$TRACE_DIR/loaded-files.jsonl"
printf '%s\n' "$SESSION_DIR/loaded-files.jsonl"
