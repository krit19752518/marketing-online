import sys
import sqlite3
import csv


def sanitize_text(s):
    if s is None:
        return None
    s = str(s)
    return s.replace('\x00', '')


def to_int(v):
    try:
        return int(float(v))
    except Exception:
        return None


def to_float(v):
    try:
        return float(v)
    except Exception:
        return None


def classify_category(title):
    if not title:
        return "หมวดหมู่อื่นๆ"
    title_lower = title.lower()
    categories = {
        "ของใช้ในบ้าน": ["ทิชชู่", "กระดาษ", "น้ำยาซักผ้า", "กล่องถนอมอาหาร", "หม้อ", "กระทะ", "ไม้แขวน", "ถังขยะ", "ทำความสะอาด", "น้ำยาล้างจาน"],
        "เครื่องใช้ไฟฟ้า & Gadget": ["ชาร์จ", "แบตสำรอง", "พัดลม", "ลำโพง", "หูฟัง", "โซล่าเซลล์", "ไฟฉาย", "โทรศัพท์", "สมาร์ทโฟน", "ปลั๊กไฟ", "สายไฟ"],
        "แฟชั่น & เครื่องแต่งกาย": ["เสื้อ", "กางเกง", "กระโปรง", "ถุงเท้า", "รองเท้า", "หมวก", "กระเป๋า", "แฟชั่น", "polo", "gq", "ขาสั้น", "ยีนส์"],
        "สุขภาพ & ความงาม": ["แมสก์", "หน้ากากอนามัย", "ครีม", "โลชั่น", "สบู่", "ยาสีฟัน", "แชมพู", "ลิป", "สกินแคร์", "เซรั่ม", "บำรุง"],
    }
    for category, keywords in categories.items():
        if any(keyword in title_lower for keyword in keywords):
            return category
    return "หมวดหมู่อื่นๆ"


def upsert_from_csv(csv_path, db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    with open(csv_path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            itemid = sanitize_text(row.get('itemid'))
            if not itemid:
                continue
            
            raw_official = row.get('is_official_shop') or ""
            raw_preferred = row.get('is_preferred_shop') or ""
            is_official = 1 if raw_official in ('1', 'True', 'true', 'Official shop') else 0
            is_preferred = 1 if raw_preferred in ('1', 'True', 'true', 'Preferred shop') else 0
            
            # Filter 1: Must be Official OR Preferred
            if is_official == 0 and is_preferred == 0:
                continue
                
            sold = to_int(row.get('item_sold'))
            rating = to_float(row.get('item_rating'))
            
            # Filter 2: Must have Sales > 50 OR Rating > 4.0
            has_sales = (sold is not None and sold > 50)
            has_good_rating = (rating is not None and rating > 4.0)
            if not (has_sales or has_good_rating):
                continue

            title = sanitize_text(row.get('title'))
            category = classify_category(title)

            params = (
                itemid,
                title,
                to_float(row.get('price')),
                to_float(row.get('sale_price')),
                to_float(row.get('discount_percentage')),
                to_int(row.get('stock')),
                sold,
                rating,
                to_int(row.get('likes_count')),
                is_official,
                is_preferred,
                1 if row.get('has_lowest_price_guarantee') in ('1', 'True', 'true') else 0,
                sanitize_text(row.get('product_link')),
                sanitize_text(row.get('product_short_link')),
                sanitize_text(row.get('image_link')),
                sanitize_text(row.get('description')),
                sanitize_text(row.get('source_filename')),
                sanitize_text(row.get('feed_date')),
                category,
            )
            cur.execute('''
            INSERT INTO shopee_affiliate_cards (
                itemid, title, price, sale_price, discount_percentage, stock,
                item_sold, item_rating, likes_count, is_official_shop,
                is_preferred_shop, has_lowest_price_guarantee, product_link,
                product_short_link, image_link, description, source_filename, feed_date,
                category
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(itemid) DO UPDATE SET
                title=excluded.title,
                price=excluded.price,
                sale_price=excluded.sale_price,
                discount_percentage=excluded.discount_percentage,
                stock=excluded.stock,
                item_sold=excluded.item_sold,
                item_rating=excluded.item_rating,
                likes_count=excluded.likes_count,
                is_official_shop=excluded.is_official_shop,
                is_preferred_shop=excluded.is_preferred_shop,
                has_lowest_price_guarantee=excluded.has_lowest_price_guarantee,
                product_link=excluded.product_link,
                product_short_link=excluded.product_short_link,
                image_link=excluded.image_link,
                description=excluded.description,
                status=CASE WHEN shopee_affiliate_cards.source_filename != excluded.source_filename THEN 'new' ELSE shopee_affiliate_cards.status END,
                ai_caption=CASE WHEN shopee_affiliate_cards.source_filename != excluded.source_filename THEN NULL ELSE shopee_affiliate_cards.ai_caption END,
                ai_prompt=CASE WHEN shopee_affiliate_cards.source_filename != excluded.source_filename THEN NULL ELSE shopee_affiliate_cards.ai_prompt END,
                source_filename=excluded.source_filename,
                feed_date=excluded.feed_date,
                category=excluded.category,
                updated_at = datetime('now')
            ''', params)

            # Record price history for this record
            cur.execute('''
            INSERT INTO shopee_price_history (itemid, price, sale_price, discount_percentage)
            VALUES (?, ?, ?, ?)
            ''', (itemid, to_float(row.get('price')), to_float(row.get('sale_price')), to_float(row.get('discount_percentage'))))
    conn.commit()
    conn.close()


def main():
    if len(sys.argv) < 3:
        print('Usage: import_csv.py <csv_path> <db_path>')
        sys.exit(1)
    csv_path = sys.argv[1]
    db_path = sys.argv[2]
    upsert_from_csv(csv_path, db_path)
    print('Import complete')


if __name__ == '__main__':
    main()
