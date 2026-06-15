#!/bin/bash
# Shopee ETL Setup Script
# This script sets up the cron job for automated ETL pipeline

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ETL_SCRIPT="$SCRIPT_DIR/shopee_etl.py"

echo "==================================================================="
echo "Shopee ETL Cron Setup"
echo "==================================================================="

# Check if script exists
if [ ! -f "$ETL_SCRIPT" ]; then
    echo "❌ Error: shopee_etl.py not found at $ETL_SCRIPT"
    exit 1
fi

# Make script executable
chmod +x "$ETL_SCRIPT"
echo "✅ Made shopee_etl.py executable"

# Create environment file
ENV_FILE="$SCRIPT_DIR/.env.shopee"
if [ ! -f "$ENV_FILE" ]; then
    cat > "$ENV_FILE" << EOF
# Shopee ETL Environment Variables
DB_HOST=localhost
DB_PORT=5432
DB_NAME=content_marketing
DB_USER=n8n_user
DB_PASSWORD=n8n_secure_password_99
SHOPEE_DATA_DIR="$SCRIPT_DIR/product-data/today-download-data"
EOF
    echo "✅ Created .env.shopee file"
else
    echo "ℹ️  .env.shopee already exists"
fi

# Create cron wrapper script
CRON_WRAPPER="$SCRIPT_DIR/run_etl.sh"
cat > "$CRON_WRAPPER" << 'EOF'
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
EOF

chmod +x "$CRON_WRAPPER"
echo "✅ Created run_etl.sh wrapper"

# Show cron job options
echo ""
echo "==================================================================="
echo "Next Steps: Add Cron Job"
echo "==================================================================="
echo ""
echo "Choose your preferred schedule:"
echo ""
echo "1️⃣  Daily at 2:00 AM:"
echo "   0 2 * * * $CRON_WRAPPER"
echo ""
echo "2️⃣  Every 6 hours:"
echo "   0 */6 * * * $CRON_WRAPPER"
echo ""
echo "3️⃣  Every day at 1:00 AM and 1:00 PM:"
echo "   0 1,13 * * * $CRON_WRAPPER"
echo ""
echo "To add cron job:"
echo "   1. Copy the desired cron line above"
echo "   2. Run: crontab -e"
echo "   3. Paste the line at the end"
echo "   4. Save and exit (:wq in vim)"
echo ""
echo "To verify cron job:"
echo "   crontab -l"
echo ""
echo "To view cron logs:"
echo "   tail -f $SCRIPT_DIR/logs/shopee_etl_*.log"
echo ""
echo "==================================================================="
