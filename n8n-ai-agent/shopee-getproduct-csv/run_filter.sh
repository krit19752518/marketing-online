#!/bin/sh
# run_filter.sh – wrapper for n8n executeCommand node "Filter Shopee CSV"
# Uses the mounted volume /data/shopee-raw-data inside the container
BASE="/data/shopee-raw-data"
# Find the newest CSV that is NOT already filtered
INPUT=$(ls -t "$BASE/today-download-data"/*.csv 2>/dev/null | grep -v shopee_filtered | head -1)
if [ -z "$INPUT" ]; then
  echo "[run_filter] No CSV file found in $BASE/today-download-data"
  exit 1
fi
OUTPUT="$BASE/today-download-data/shopee_filtered_$(date +%Y%m%d).csv"
echo "[run_filter] Using input: $INPUT"
echo "[run_filter] Output will be: $OUTPUT"
# Execute the Python filter script (already placed in the same directory inside the container)
SCRIPT_DIR=$(dirname "$0")
PYTHON="/usr/bin/python3"
"$PYTHON" "$SCRIPT_DIR/filter_csv.py" --input "$INPUT" --output "$OUTPUT"
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
  echo "[run_filter] filter_csv.py failed with exit code $EXIT_CODE"
fi
exit $EXIT_CODE
