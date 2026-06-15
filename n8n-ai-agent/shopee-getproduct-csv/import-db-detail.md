# Shopee ETL Pipeline - รายละเอียดขั้นตอน

## 📋 ภาพรวม: เรากำลังทำอะไร?

เป้าหมายหลัก: **ดึงข้อมูลสินค้า Shopee → กรอง → นำเข้า Database อัตโนมัติ**

### ❌ ปัญหาเดิม (ใช้ N8N):
- UTF-8 Encoding errors ทุกครั้ง
- CSV มี null bytes (`0x00`) ที่ PostgreSQL ไม่รับ
- Error ที่บรรทัดที่ 10,015 ขึ้นไป
- N8N ไม่มี error handling ที่ดี

### ✅ วิธีแก้: Standalone Python + Cron
- Clean CSV ที่ระดับ binary ก่อน processing
- Filter ตามเกณฑ์ business logic
- Import ด้วย PostgreSQL COPY (เร็วและเชื่อถือได้)
- Automated logging และ archival

---

## 🔄 ขั้นตอน 5 ของ Pipeline

```
Step 1: CLEAN
  Input: shopee_raw.csv (มี null bytes ❌)
  ↓
  - Binary read file
  - ลบ \x00 ทั้งหมด
  - ลบ control characters
  - Try UTF-8 decode (สำรอง: latin-1, cp1252)
  ↓
  Output: shopee_cleaned.csv (เสียบ✅)

Step 2: FILTER
  Input: shopee_cleaned.csv
  ↓
  - DictReader (CSV → dict rows)
  - ตรวจสอบเกณฑ์แต่ละแถว
  - Map column names (เช่น "like" → "likes_count")
  - Clean field values
  ↓
  Output: shopee_filtered_YYYYMMDD.csv ใน product-data/

Step 3: SANITIZE
  Input: Filtered rows
  ↓
  - ลบ null bytes จาก text fields
  - ลบ tab, newline, carriage return ที่ไม่ต้องการ
  - Escape quotes ให้ถูก
  - ตรวจสอบ data types
  ↓
  Output: Safe data ready for DB

Step 4: IMPORT
  Input: Sanitized rows
  ↓
  - Connect PostgreSQL
  - TRUNCATE shopee_discount_products (ลบเก่า)
  - COPY FROM STDIN (bulk import)
  - Verify row count
  ↓
  Output: Data in DB ✅

Step 5: ARCHIVE
  Input: Processed files
  ↓
  - Move raw CSV → /old-data/
  - Move filtered CSV → /use-data/
  - Keep logs in /logs/
  ↓
  Output: Clean directory structure
```

---

## 🎯 Filter Logic (ขั้นตอน 2)

### เกณฑ์ที่ include สินค้า:

```python
Include product IF:
  (discount_percentage > 30%) OR
  (has_lowest_price_guarantee == 'Yes') OR
  ((is_official_shop == 'Official shop' OR is_preferred_shop == 'Preferred shop') AND discount_percentage > 0%)
```

### ตัวอย่าง:
```
Product A: discount = 45% ✅ Include (> 30%)
Product B: discount = 25%, lowest_price = 'Yes' ✅ Include
Product C: discount = 5%, official_shop = 'Yes' ✅ Include
Product D: discount = 0%, normal_shop ❌ Exclude
```

---

## 🗄️ Database Operations (ขั้นตอน 4)

### Connection:
```python
host = 'localhost'
port = 5432
database = 'content_marketing'
user = 'n8n_user'
password = 'n8n_secure_password_99'
```

### Table: `shopee_discount_products`
- 25 columns
- Primary Key: `itemid`
- TRUNCATE before each import (ล้างเก่าทั้งหมด)

### Import Process:
```sql
BEGIN;
  TRUNCATE TABLE shopee_discount_products;
  COPY shopee_discount_products FROM STDIN 
    WITH (FORMAT csv, DELIMITER ',', NULL '');
COMMIT;
```

### Verification:
```python
# ตรวจสอบจำนวน rows
SELECT COUNT(*) FROM shopee_discount_products;
# Expected: 10,000 - 50,000 (ขึ้นอยู่กับ filter)
```

---

## 📝 Logging (ในทุกขั้น)

### Log Format:
```
logs/shopee_etl_YYYYMMDD_HHMMSS.log
logs/shopee_etl_latest.log
```

### ดูแบบ realtime:
```bash
tail -f logs/shopee_etl_latest.log
```

### ตัวอย่าง Log:
```
2026-06-09 14:30:15,123 - INFO - ===== SHOPEE ETL PIPELINE START =====
2026-06-09 14:30:15,150 - INFO - ✅ Database connected
2026-06-09 14:30:15,200 - INFO - Found CSV: shopee_raw_20260609.csv (12.5 MB)

2026-06-09 14:30:15,300 - INFO - [STEP 1] CLEANING CSV...
2026-06-09 14:30:15,500 - INFO - Original: 12,567,890 bytes
2026-06-09 14:30:16,100 - INFO - Removed 45,230 null bytes
2026-06-09 14:30:16,500 - INFO - Cleaned: 12,522,660 bytes
2026-06-09 14:30:16,600 - INFO - ✅ Clean complete

2026-06-09 14:30:16,700 - INFO - [STEP 2] FILTERING PRODUCTS...
2026-06-09 14:30:30,000 - INFO - Total rows: 100,000
2026-06-09 14:30:30,100 - INFO - Matched criteria: 25,000
2026-06-09 14:30:30,200 - INFO - ✅ Filter complete

2026-06-09 14:30:30,300 - INFO - [STEP 3] SANITIZING DATA...
2026-06-09 14:30:32,000 - INFO - All rows sanitized
2026-06-09 14:30:32,100 - INFO - ✅ Sanitize complete

2026-06-09 14:30:32,200 - INFO - [STEP 4] IMPORTING TO DATABASE...
2026-06-09 14:30:32,300 - INFO - TRUNCATE shopee_discount_products
2026-06-09 14:30:32,400 - INFO - Executing COPY command...
2026-06-09 14:30:45,000 - INFO - ✅ Import complete
2026-06-09 14:30:45,100 - INFO - Total rows in DB: 25,000

2026-06-09 14:30:45,200 - INFO - [STEP 5] ARCHIVING FILES...
2026-06-09 14:30:45,300 - INFO - Moved CSV → /old-data/
2026-06-09 14:30:45,400 - INFO - Moved filtered → /use-data/
2026-06-09 14:30:45,500 - INFO - ✅ Archive complete

2026-06-09 14:30:45,600 - INFO - ===== SHOPEE ETL PIPELINE COMPLETED SUCCESSFULLY =====
2026-06-09 14:30:45,700 - INFO - Duration: 30.4 seconds
2026-06-09 14:30:45,800 - INFO - Exit code: 0
```

---

## 🔌 Environment Variables

| Variable | ค่า Default | อธิบาย |
|----------|------------|--------|
| `DB_HOST` | localhost | PostgreSQL server address |
| `DB_PORT` | 5432 | PostgreSQL port |
| `DB_NAME` | content_marketing | Database name |
| `DB_USER` | n8n_user | Database user |
| `DB_PASSWORD` | n8n_secure_password_99 | Database password |
| `SHOPEE_DATA_DIR` | /data/shopee-raw-data/today-download-data | Input CSV directory |

### ตั้งค่า:
```bash
# ไฟล์ .env.shopee
export DB_HOST=localhost
export DB_PORT=5432
...
```

---

## ⏰ Automation (Cron Job)

### Setup:
```bash
bash setup_cron.sh
```

### Schedule Example (Daily 2 AM):
```cron
0 2 * * * /home/krit/my-office/n8n-ai-agent/shopee-getproduct-csv/run_etl.sh
```

### Execution Flow:
```
Cron fires (2:00 AM daily)
  ↓
run_etl.sh (wrapper script)
  - Source .env.shopee
  - Python3 shopee_etl.py
  ↓
Python script runs (สูงสุด 2 นาที)
  ↓
Log saved to logs/shopee_etl_*.log
  ↓
Success or Failure (exit code 0 or 1)
```

---

## 🧪 Testing Checklist

- [ ] `pip install -r requirements.txt` ✅
- [ ] `bash setup_cron.sh` ✅
- [ ] Manual run: `python3 shopee_etl.py` ✅
- [ ] Check logs: `tail -f logs/shopee_etl_*.log` ✅
- [ ] Verify DB: `SELECT COUNT(*) FROM shopee_discount_products;` ✅
- [ ] Add cron: `crontab -e` ✅
- [ ] Monitor first run ✅
- [ ] Verify archive directories ✅

---

## 📊 Performance Metrics

### Expected Timing:
- **Clean**: 5-10 seconds (อัตราส่วน ขึ้นอยู่กับขนาด CSV)
- **Filter**: 10-15 seconds
- **Import**: 5-10 seconds
- **Archive**: 1-2 seconds
- **Total**: 20-40 seconds

### File Sizes:
- **Input CSV**: 10-50 MB (ขึ้นอยู่ on daily data)
- **After clean**: -2% to -5% (null bytes removed)
- **After filter**: -70% to -80% (only matched products)

---

## 🚨 Error Handling

| Error | Handling |
|-------|----------|
| CSV not found | Log error + exit code 1 |
| DB connection fail | Log error + exit code 1 |
| Encoding issue | Try fallback encodings + log warning |
| Import fail | ROLLBACK + log detailed error |
| No matched products | Continue (valid result) + log info |

---

## 🎯 Success Criteria

✅ Pipeline succeeds IF:
1. CSV file สามารถ clean ได้ (no encoding errors)
2. Database connection successful
3. สินค้าอย่างน้อย 100 items ตรงเกณฑ์
4. Rows imported == rows filtered
5. Archive directories เต็มไป
6. Exit code = 0

---

## 📞 Troubleshooting Guide

### CSV not found:
```bash
ls /data/shopee-raw-data/today-download-data/
# Upload CSV if empty
```

### DB Connection Failed:
```bash
psql -h localhost -U n8n_user -d content_marketing -c "SELECT 1"
# Check if PostgreSQL running
docker ps | grep postgres
```

### Encoding Error:
```bash
# Check logs for details
cat logs/shopee_etl_*.log | grep -i error
# Might be invalid UTF-8 in source
```

### No Products Matched:
```bash
# Check filter logic
grep "def should_include" shopee_etl.py
# May need to adjust discount threshold
```

---

**เวอร์ชัน**: 1.0  
**สร้าง**: 2026-06-09  
**สถานะ**: 🟢 Ready for Production
