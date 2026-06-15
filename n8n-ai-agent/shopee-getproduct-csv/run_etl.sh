#!/bin/bash
# Cron wrapper for Shopee ETL

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env.shopee"

# Load environment
if [ -f "$ENV_FILE" ]; then
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs)
fi

# Run ETL
python3 "$SCRIPT_DIR/shopee_etl.py"
