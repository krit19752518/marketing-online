import os
import json
import sqlite3
import urllib.request
import logging

DB_PATH = os.getenv('DATABASE_PATH', 'facebook-post.db')
PAGE_ACCESS_TOKEN = os.getenv('FB_PAGE_ACCESS_TOKEN', 'YOUR_PAGE_ACCESS_TOKEN')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def search_products(keyword=None, campaign=None, limit=10):
    """
    Search database for approved items by keyword or campaign.
    """
    conn = get_db()
    cursor = conn.cursor()
    query = "SELECT title, price, sale_price, discount_percentage, item_rating, product_short_link, product_link, image_link FROM shopee_affiliate_cards WHERE status = 'approved'"
    params = []
    
    if campaign:
        query += " AND source_filename = ?"
        params.append(campaign)
    elif keyword:
        query += " AND (title LIKE ? OR description LIKE ?)"
        # Match pattern for LIKE search
        like_pattern = f"%{keyword}%"
        params.extend([like_pattern, like_pattern])
        
    query += " ORDER BY discount_percentage DESC, updated_at DESC LIMIT ?"
    params.append(limit)
    
    try:
        cursor.execute(query, params)
        rows = [dict(r) for r in cursor.fetchall()]
        return rows
    except Exception as e:
        logging.error(f"[Chatbot] Database query failed: {e}")
        return []
    finally:
        conn.close()

def send_messenger_api(payload):
    """
    Send HTTP POST payload to Facebook Messenger Send API.
    """
    url = f"https://graph.facebook.com/v19.0/me/messages?access_token={PAGE_ACCESS_TOKEN}"
    headers = {"Content-Type": "application/json"}
    body_data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(url, data=body_data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            res_body = res.read().decode('utf-8')
            logging.info(f"[Chatbot] Message sent successfully: {res_body}")
            return True
    except Exception as e:
        logging.error(f"[Chatbot] Failed to send Messenger message: {e}")
        if hasattr(e, 'read'):
            logging.error(f"[Chatbot] Error details: {e.read().decode('utf-8')}")
        return False

def build_carousel_payload(sender_psid, items, title_prefix=""):
    """
    Build Facebook Generic Template Carousel payload.
    """
    if not items:
        # Fallback to text message if no items found
        return {
            "recipient": {"id": sender_psid},
            "message": {
                "text": "ไม่พบดีลสินค้าที่คุณต้องการเลยค่ะในขณะนี้ ลองค้นหาด้วยคำอื่นๆ ดูนะคะ 🔍"
            }
        }
        
    elements = []
    for item in items:
        title = item.get('title') or "ดีลพิเศษ Shopee"
        # Truncate title to fit Facebook's limit (80 characters)
        if len(title) > 75:
            title = title[:72] + "..."
            
        discount = item.get('discount_percentage')
        sale_price = item.get('sale_price')
        price = item.get('price')
        rating = item.get('item_rating') or '4.8'
        
        # Format subtitle with price and rating info
        subtitle = f"ลดเหลือ {sale_price or '0'}.- (ปกติ {price or '0'}.-) | ส่วนลด {discount or '0'}% | รีวิว {rating} ดาว ⭐"
        if len(subtitle) > 80:
            subtitle = subtitle[:77] + "..."
            
        link = item.get('product_short_link') or item.get('product_link') or "https://shopee.co.th"
        image = item.get('image_link') or "https://cf.shopee.co.th/file/" # Fallback image
        
        element = {
            "title": title,
            "image_url": image,
            "subtitle": subtitle,
            "default_action": {
                "type": "web_url",
                "url": link,
                "webview_height_ratio": "full"
            },
            "buttons": [
                {
                    "type": "web_url",
                    "url": link,
                    "title": "🛒 ช็อปเลยที่ Shopee"
                }
            ]
        }
        elements.append(element)
        
    return {
        "recipient": {"id": sender_psid},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": elements
                }
            }
        }
    }

def send_text_message(sender_psid, text):
    """
    Utility helper to send a simple text message.
    """
    payload = {
        "recipient": {"id": sender_psid},
        "message": {"text": text}
    }
    return send_messenger_api(payload)

def handle_chatbot_message(sender_psid, message_text):
    """
    Process incoming text messages (search request or help).
    """
    message_text = message_text.strip().lower()
    
    # Check if the user is asking for campaigns
    if message_text in ("grade aaa", "aaa", "เกรด aaa", "เกรดaaa"):
        items = search_products(campaign="GRADE AAA")
        payload = build_carousel_payload(sender_psid, items)
        return send_messenger_api(payload)
        
    elif message_text in ("volume shock", "volume", "shock", "ล้างสต็อก"):
        items = search_products(campaign="VOLUME SHOCK")
        payload = build_carousel_payload(sender_psid, items)
        return send_messenger_api(payload)
        
    elif message_text in ("micro-trigger", "micro", "trigger", "ดีลล่าแต้ม", "ราคาจิ๋ว"):
        items = search_products(campaign="MICRO-TRIGGER")
        payload = build_carousel_payload(sender_psid, items)
        return send_messenger_api(payload)
        
    elif message_text in ("เริ่มใช้งาน", "help", "เมนู", "สวัสดี", "hello", "hi"):
        return send_welcome_message(sender_psid)
        
    # Standard keyword search
    logging.info(f"[Chatbot] Querying search term: '{message_text}' for user: {sender_psid}")
    items = search_products(keyword=message_text)
    payload = build_carousel_payload(sender_psid, items)
    return send_messenger_api(payload)

def handle_chatbot_postback(sender_psid, payload_text):
    """
    Process click events on Postback buttons.
    """
    logging.info(f"[Chatbot] Received postback: '{payload_text}' from user: {sender_psid}")
    if payload_text == "GET_STARTED_PAYLOAD":
        return send_welcome_message(sender_psid)
        
    elif payload_text == "CAMP_GRADE_AAA":
        items = search_products(campaign="GRADE AAA")
        payload = build_carousel_payload(sender_psid, items)
        return send_messenger_api(payload)
        
    elif payload_text == "CAMP_VOLUME_SHOCK":
        items = search_products(campaign="VOLUME SHOCK")
        payload = build_carousel_payload(sender_psid, items)
        return send_messenger_api(payload)
        
    elif payload_text == "CAMP_MICRO_TRIGGER":
        items = search_products(campaign="MICRO-TRIGGER")
        payload = build_carousel_payload(sender_psid, items)
        return send_messenger_api(payload)
        
    return send_text_message(sender_psid, "ระบบไม่เข้าใจคำสั่งนี้ค่ะ")

def send_welcome_message(sender_psid):
    """
    Send standard welcome message with button choices.
    """
    payload = {
        "recipient": {"id": sender_psid},
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "button",
                    "text": "สวัสดีค่ะ! ยินดีต้อนรับสู่ RateDeeDee 📊 ระบบเรดาร์ล่าของหลุดและสแกนราคาจริง\n\nพิมพ์ของที่ต้องการค้นหา หรือเลือกดูแคมเปญสินค้าพิเศษผ่านปุ่มด้านล่างได้เลยค่ะ:",
                    "buttons": [
                        {
                            "type": "postback",
                            "title": "🟢 เกรดพรีเมียม GRADE AAA",
                            "payload": "CAMP_GRADE_AAA"
                        },
                        {
                            "type": "postback",
                            "title": "🔴 ล้างสต็อก VOLUME SHOCK",
                            "payload": "CAMP_VOLUME_SHOCK"
                        },
                        {
                            "type": "postback",
                            "title": "⚡ ราคาจิ๋ว MICRO-TRIGGER",
                            "payload": "CAMP_MICRO_TRIGGER"
                        }
                    ]
                }
            }
        }
    }
    return send_messenger_api(payload)
