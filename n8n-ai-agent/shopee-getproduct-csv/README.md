# Shopee ETL Pipeline (Standalone)

ระบบ ETL ที่ทำงานอัตโนมัติสำหรับดึง กรอง และ import ข้อมูลสินค้า Shopee ไปยังฐานข้อมูล PostgreSQL

## 📊 ฟังก์ชันหลัก

```
Raw CSV → Clean (remove null bytes) → Filter (discount > 30%) → Import to DB
```

### ขั้นตอนการทำงาน

1. **Clean CSV** - ลบ null bytes และเพิ่มเติม encoding issues
2. **Filter** - คัดเลือกเฉพาะสินค้าที่ตรงเกณฑ์
   - Discount > 30% OR
   - Lowest Price Guarantee = Yes OR  
   - (Official/Preferred shop) + Discount > 0%
3. **Sanitize** - ทำความสะอาดข้อมูลทุก field
4. **Import** - COPY ไปยัง `shopee_discount_products` table
5. **Archive** - ย้ายไฟล์ไปโฟลเดอร์ `/old-data` และ `/use-data`

---

## 🚀 Quick Start

### 1. ติดตั้ง Dependencies

```bash
# Install PostgreSQL driver
pip3 install psycopg2-binary

# Or use requirements.txt
pip3 install -r requirements.txt
```

### 2. ตั้งค่า Environment Variables

สร้างไฟล์ `.env.shopee`:
```bash
bash setup_cron.sh
```

จะสร้าง `.env.shopee` ที่มี default values:
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=content_marketing
DB_USER=n8n_user
DB_PASSWORD=n8n_secure_password_99
SHOPEE_DATA_DIR=$(pwd)/product-data/today-download-data
```

แก้ไข values ให้ตรงกับระบบของคุณ:
```bash
vi .env.shopee
```

### 3. ทดลองรันด้วยตนเอง

```bash
# Run once manually
python3 shopee_etl.py

# Or with env file
source .env.shopee && python3 shopee_etl.py
```

### 3.1 ดู Log แบบ Real-time

```bash
tail -f logs/shopee_etl_latest.log
```

หรือถ้าต้องการดูไฟล์ timestamped log ล่าสุด:

```bash
ls -1tr logs/shopee_etl_*.log | tail -n 1 | xargs tail -f
```

### 4. ตั้งค่า Cron Job (Automation)

```bash
# Setup cron wrapper
bash setup_cron.sh

# Edit crontab
crontab -e
```

เลือก schedule จากตัวเลือกด้านล่าง และ paste ลงใน crontab

**ตัวอย่าง: ทุกวัน 2:00 AM**
```cron
0 2 * * * /home/krit/my-office/n8n-ai-agent/shopee-getproduct-csv/run_etl.sh
```

### 5. ตรวจสอบ Logs

```bash
# View latest log
tail -f logs/shopee_etl_*.log

# Or specific date
ls -lh logs/
cat logs/shopee_etl_20260609_020000.log
```

---

## 📁 File Structure

```
shopee-getproduct-csv/
├── shopee_etl.py              # Main ETL script
├── setup_cron.sh              # Cron setup helper
├── run_etl.sh                 # Cron wrapper (generated)
├── .env.shopee                # Environment config (generated)
├── requirements.txt           # Python dependencies
├── logs/                      # Log files directory (generated)
│   └── shopee_etl_*.log
├── temp/                      # Temporary cleaned CSV (generated)
│   └── shopee_cleaned.csv
└── product-data/              # Data directories
│   └── today-download-data/   # Input CSV
│   └── old-data/              # Archived raw CSV
│   └── use-data/              # Archived filtered CSV
```

---

## ⚙️ Configuration

### Database Connection

```python
DB_HOST = 'localhost'       # PostgreSQL host
DB_PORT = '5432'            # PostgreSQL port
DB_NAME = 'content_marketing'  # Database name
DB_USER = 'n8n_user'        # Database user
DB_PASSWORD = '...'         # Database password
```

### Directory Paths

```python
DATA_DIR = '/data/shopee-raw-data/today-download-data'  # Input/output
LOG_DIR = './logs'          # Log files
TEMP_DIR = './temp'         # Temporary files
```

### Filter Criteria

Edit `filter_products()` function to customize:

```python
def should_include(row):
    # Condition 1: Discount > 30%
    if int(row.get('discount_percentage', 0)) > 30:
        return True
    
    # Condition 2: Lowest Price Guarantee
    if row.get('has_lowest_price_guarantee') == 'Yes':
        return True
    
    # Condition 3: Official/Preferred shop + discount
    if row.get('is_official_shop') == 'Official shop':
        if int(row.get('discount_percentage', 0)) > 0:
            return True
    
    return False
```

---

## 🐛 Troubleshooting

### Error: `CSV file not found`

```bash
# Check data directory
ls -la /data/shopee-raw-data/today-download-data/

# If empty, upload or create test CSV
cp /path/to/shopee_raw.csv /data/shopee-raw-data/today-download-data/
```

### Error: `Connection refused` (Database)

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Or for local PostgreSQL
psql -h localhost -U n8n_user -d content_marketing -c "SELECT 1"
```

### Error: `Module psycopg2 not found`

```bash
# Install dependency
pip3 install psycopg2-binary
```

### Error: `Invalid byte sequence for encoding UTF8`

This is already handled in `shopee_etl.py` via:
1. Binary file read
2. Null byte removal
3. UTF-8 error replacement
4. Proper stream sanitization

Check logs for details:
```bash
cat logs/shopee_etl_*.log | grep -i "error"
```

---

## 📊 Database Schema

Table: `shopee_discount_products`

| Column | Type | Notes |
|--------|------|-------|
| itemid (PK) | BIGINT | Product ID |
| title | TEXT | Product name |
| price | NUMERIC | Original price |
| sale_price | NUMERIC | Discounted price |
| discount_percentage | INT | Discount % |
| discount_percentage | INT | Discount % |
| item_sold | INT | Units sold |
| item_rating | NUMERIC | Star rating (0-5) |
| is_official_shop | VARCHAR | Official shop? |
| has_lowest_price_guarantee | VARCHAR | Price guarantee? |
| ... | ... | 20+ columns total |

---

## ⏰ Cron Schedule Examples

```cron
# Daily at 2 AM
0 2 * * * /path/to/run_etl.sh

# Every 6 hours
0 */6 * * * /path/to/run_etl.sh

# Daily at 1 AM and 1 PM
0 1,13 * * * /path/to/run_etl.sh

# Every weekday at 8 AM
0 8 * * 1-5 /path/to/run_etl.sh

# Every Sunday at midnight
0 0 * * 0 /path/to/run_etl.sh
```

**Cron field format:**
```
┌───────────── minute (0 - 59)
│ ┌───────────── hour (0 - 23)
│ │ ┌───────────── day of month (1 - 31)
│ │ │ ┌───────────── month (1 - 12)
│ │ │ │ ┌───────────── day of week (0 - 6) (Sunday to Saturday)
│ │ │ │ │
│ │ │ │ │
* * * * * command
```

---

## 🔍 Monitoring

### View Active Cron Jobs

```bash
crontab -l
```

### Check Cron Execution History

```bash
# Last 50 lines
grep CRON /var/log/syslog | tail -50

# Or on macOS
log stream --predicate 'process == "cron"' --level debug
```

### Monitor Real-time Logs

```bash
# Watch latest log
watch -n 1 'tail -n 20 logs/shopee_etl_*.log'

# Or continuous tail
tail -f logs/shopee_etl_$(date +%Y%m%d)*.log
```

---

## 🛠️ Manual Operations

### Run ETL Pipeline

```bash
python3 shopee_etl.py
```

### Run with Custom Config

```bash
# Override environment variables
DB_HOST=192.168.1.100 \
DB_PORT=5432 \
DB_NAME=my_database \
python3 shopee_etl.py
```

### Check Database

```bash
# Connect to database
psql -h localhost -U n8n_user -d content_marketing

# Inside psql:
SELECT COUNT(*) FROM shopee_discount_products;
SELECT * FROM shopee_discount_products LIMIT 5;
```

---

## 📝 Logging

Logs are stored in `logs/` directory with format:
```
shopee_etl_YYYYMMDD_HHMMSS.log
```

Log levels:
- **INFO** - Normal operation
- **WARNING** - Non-critical issues
- **ERROR** - Critical failures (pipeline stops)

Example log:
```
2026-06-09 14:30:15,123 - INFO - ==================================================
2026-06-09 14:30:15,124 - INFO - SHOPEE ETL PIPELINE START
2026-06-09 14:30:15,200 - INFO - Found input CSV: shopee_raw_20260609.csv
2026-06-09 14:30:15,300 - INFO - Cleaning CSV file: ...
2026-06-09 14:30:15,500 - INFO - Original file size: 1,234,567 bytes
2026-06-09 14:30:15,600 - INFO - Cleaned file size: 1,200,000 bytes
2026-06-09 14:31:00,100 - INFO - Filtering complete. Total: 100,000, Matched: 25,000
2026-06-09 14:31:30,200 - INFO - Import complete! Total rows in DB: 25,000
```

---

## 🚨 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| CSV not found | Data directory empty | Upload CSV file first |
| DB connection failed | PostgreSQL down | Start PostgreSQL container/service |
| No matching products | Filter too strict | Review filter criteria |
| OOM error | Large CSV file | Increase system RAM or split file |
| Encoding errors | Invalid UTF-8 | Already handled, check logs |

---

## 🔄 From N8N to This Solution

**Why move from N8N?**

| Aspect | N8N | Standalone |
|--------|-----|-----------|
| Setup | Complex UI | Simple Python |
| Error handling | Limited | Full control |
| Monitoring | Web UI | Logs + Cron |
| Debugging | Difficult | Easy terminal |
| Performance | Moderate | Fast |
| Learning curve | Steep | Gentle |

---

## 📞 Support

For issues or questions:

1. Check logs first: `tail -f logs/shopee_etl_*.log`
2. Review troubleshooting section above
3. Check database connection: `psql -h localhost -U n8n_user -d content_marketing -c "SELECT 1"`
4. Test manually: `python3 shopee_etl.py`

---

## 📄 License

Internal use only

**Version:** 1.0  
**Last Updated:** 2026-06-09
