#!/usr/bin/env bash
# Fetch the archived Z.ai CVD ledger page from the Wayback Machine.
# Usage: scripts/fetch.sh [output.html]
set -euo pipefail

URL="https://web.archive.org/web/20260814211237/https://cvd.z.ai/ledger/"
OUT="${1:-raw/ledger-20260814.html}"

mkdir -p "$(dirname "$OUT")"
curl -fsSL --retry 5 --retry-delay 5 "$URL" -o "$OUT"
echo "Fetched $(wc -c < "$OUT" | tr -d ' ') bytes -> $OUT"
