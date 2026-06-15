#!/bin/sh
set -euo pipefail
# move_files.sh – archive raw CSV and filtered CSV
# Arguments:
#   $1 = path to raw CSV (today-download-data)
#   $2 = path to filtered CSV (today-download-data)

RAW="$1"
FILTERED="$2"

ROOT="/data/shopee-raw-data"

mkdir -p "$ROOT/old-data" "$ROOT/use-data"

if [ -f "$RAW" ]; then
  mv -f "$RAW" "$ROOT/old-data/$(basename "$RAW")"
  echo "[move_files] Moved raw CSV to old-data: $(basename "$RAW")"
else
  echo "[move_files] Raw file NOT found (skipping): $RAW"
fi

if [ -f "$FILTERED" ]; then
  mv -f "$FILTERED" "$ROOT/use-data/$(basename "$FILTERED")"
  echo "[move_files] Moved filtered CSV to use-data: $(basename "$FILTERED")"
else
  echo "[move_files] Filtered file NOT found (skipping): $FILTERED"
fi
