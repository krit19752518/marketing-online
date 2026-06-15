#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -f "$DATABASE_PATH" ]; then
  echo "Initializing database..."
  sqlite3 "$DATABASE_PATH" < migrations/001_create_shopee_affiliate_cards.sql
fi
echo "Starting Flask app on :5000"
python3 app.py
