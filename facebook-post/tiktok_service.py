"""
tiktok_service.py
-----------------
Provides:
  - generate_tiktok_caption(card) -> calls local Ollama with a combined prompt,
                                     returns structured Thai script and English image prompts.
  - compose_tiktok_slide_image(bg_image_path, product_image_url, text_content, output_path, slide_num, price_info=None)
                                     -> uses Pillow to compose the final image:
                                        overlays the product image and overlays the text in the top 60% area.
"""

import os
import json
import urllib.request
import logging
import re
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageStat

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_ollama_model():
    """Auto-detect the best available Ollama model."""
    ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    try:
        req = urllib.request.Request(f"{ollama_url}/api/tags")
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            for preferred in ["llama3.2:3b", "llama3.2", "llama3"]:
                if preferred in models:
                    return preferred
            if models:
                return models[0]
    except Exception:
        pass
    return "llama3.2:3b"


def clean_product_text(text: str) -> str:
    if not text:
        return ""
    # Strip common infographics like 2%, 5% AHA, 10g, 465ml, 8D, etc.
    # Match number + unit (%, g, ml, มล, d, D, etc.)
    cleaned = re.sub(r'\d+\s*(?:%|g|ml|มล|d|G|ML|D)\b', '', text)
    # Match isolated percentages
    cleaned = re.sub(r'\b\d+%\b', '', cleaned)
    # Match promo texts
    cleaned = re.sub(r'ลด\s*\d+%\s*|แถมฟรี\s*', '', cleaned)
    # Clean extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def get_product_anatomy_en(title: str, category: str) -> str:
    """
    Analyzes title and category text to deterministically return a detailed
    English anatomical definition of the product to prevent visual semantic/halo drift.
    """
    title_lower = title.lower()
    cat_lower = category.lower()
    
    # 1. Check title keywords for specific product categories
    if any(x in title_lower for x in ["innerdeo", "persimmon", "ลดกลิ่นกาย"]):
        return "A white plastic supplement medicine pill bottle jar with a white screw cap lid"
    if any(x in title_lower for x in ["skintific", "cushion", "คุชชั่น"]):
        return "A premium round gold metallic cosmetic cushion compact casing (SKINTIFIC brand) sitting open or closed showing its sleek design"
    if any(x in title_lower for x in ["yuedpao", "ยืดเปล่า"]):
        return "A premium pair of black athletic running shorts (Yuedpao brand)"
    if any(x in title_lower for x in ["nivea", "นีเวีย", "luminous", "ลูมินัส", "630"]):
        return "A white Nivea Luminous 630 skin fluid bottle with a gold metallic cap"
    if any(x in title_lower for x in ["hygiene", "ไฮยีน", "fabric freshener", "สเปรย์ฉีดผ้า", "fabric spray"]):
        return "A household fabric freshener spray bottle with a white trigger spray mechanism (foggy spray head)"
    if any(x in title_lower for x in ["vaseline", "pro derma", "lotion", "โลชั่น", "บำรุงผิว"]) and not any(x in title_lower for x in ["innerdeo", "อาหารเสริม", "supplement", "powder"]):
        if any(x in title_lower for x in ["gluta-hya", "กลูต้า-ไฮยา", "tube", "หลอด"]):
            return "A premium flat plastic squeeze tube packaged lotion, standing vertically upside down upon its white cap, featuring the authentic Vaseline Gluta-Hya branding colors."
        return "A commercial lotion bottle with a pump dispenser head"
    if any(x in title_lower for x in ["serum", "เซรั่ม", "essence", "เอสเซนส์"]) and not any(x in title_lower for x in ["innerdeo", "อาหารเสริม", "supplement"]):
        return "A skincare serum glass bottle with a rubber dropper cap"
    if any(x in title_lower for x in ["adapter", "charger", "ชาร์จ", "หัวชาร์จ", "usb-c"]):
        return "A compact white wall charger power adapter block"
    if any(x in title_lower for x in ["power bank", "powerbank", "พาวเวอร์แบงค์", "แบตเตอรี่สำรอง"]):
        return "A flat rectangular portable battery power bank"
    if any(x in title_lower for x in ["diaper", "mamypoko", "แพมเพิส", "ผ้าอ้อม", "กางเกงผ้าอ้อม"]):
        return "A plastic packaging bag containing baby diapers"
    if any(x in title_lower for x in ["detergent", "เปา", "pao", "ผงซักฟอก", "น้ำยาซักฟอก", "ซักผ้า"]):
        return "A soft packaging pouch bag containing laundry detergent"
    if any(x in title_lower for x in ["ยางรัดผม", "โดนัทรัดผม", "scrunchies", "hair tie", "กิ๊บติดผม", "กิ๊บ"]):
        return "A pack of colorful elastic fabric hair scrunchies and cute hair ties"
    if any(x in title_lower for x in ["coffee", "กาแฟ"]):
        return "A sealed coffee bag pouch"
    if any(x in title_lower for x in ["shampoo", "ยาสระผม", "แชมพู"]):
        return "A shampoo bottle with a dispenser cap"
    if any(x in title_lower for x in ["sensor", "night light", "puck light", "ไฟเซ็นเซอร์", "โคมไฟ"]):
        return "A sleek, minimal white circular motion-sensor puck light, showing its smooth frosted plastic diffuser front and modern round chassis design."
    if any(x in title_lower for x in ["sunscreen", "กันแดด", "dd cream", "ดีดีครีม", "watermelon", "แตงโม", "jula"]):
        return "A dynamic pink cream sachet pouch with a prominent white plastic twist-cap closure at the top, showing Jula's Herb Watermelon DD Cream branding."
        
    # 2. Check category keywords (Thai / English)
    if any(x in cat_lower for x in ["fashion", "apparel", "แฟชั่น", "เครื่องแต่งกาย"]):
        return "A premium clothing apparel item"
    if any(x in cat_lower for x in ["beauty", "skincare", "ความงาม", "เครื่องสำอาง"]) and not any(x in title_lower or x in cat_lower for x in ["อาหารเสริม", "supplement", "dietary", "innerdeo"]):
        return "A skincare cosmetics bottle"
    if any(x in cat_lower for x in ["electronics", "อุปกรณ์", "คอมพิวเตอร์", "มือถือ"]):
        return "An electronic hardware device"
    if any(x in cat_lower for x in ["home", "laundry", "ซักรีด", "ของใช้ในบ้าน"]):
        return "A household product package"
        
    # 3. Fallback generic product token using dynamic title
    cleaned_title = clean_product_text(title)
    return f"A retail package of {cleaned_title}"

# ---------------------------------------------------------------------------
# Dynamic Slide 2 Copywriting Refresher (Value Copy) & Sanitization
# ---------------------------------------------------------------------------

def clean_state(text: str) -> str:
    """
    Variable Lexical Sanitization: Fully deletes and nullifies the terms:
    'watermelon', 'jula's herb', 'sachet', 'pouch', 'pink', 'red'.
    """
    if not text:
        return ""
    import re
    # Forbidden words (case-insensitive)
    forbidden = ["watermelon", "jula's herb", "sachet", "pouch", "pink", "red"]
    cleaned = text
    for word in forbidden:
        pattern = re.compile(re.escape(word), re.IGNORECASE)
        cleaned = pattern.sub("", cleaned)
    # Clean up double commas, trailing commas, or broken lists (e.g. "any , , or" -> "any or")
    cleaned = re.sub(r',\s*,', ',', cleaned)
    cleaned = re.sub(r',\s*or\b', ' or', cleaned)
    cleaned = re.sub(r'\bany\s+or\b', 'or', cleaned)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def generate_slide_2_value_text(price_info: dict) -> str:
    """
    Generates Slide 2's Thai value copywriting dynamically from a curated array,
    cleaning float numbers to integers and replacing placeholders.
    """
    import secrets
    import logging
    
    def clean_int(val) -> int:
        if val is None:
            return 0
        s = str(val).strip()
        s = s.replace("%", "").strip()
        if not s:
            return 0
        try:
            return int(float(s))
        except ValueError:
            return 0
            
    # 1. Price Format Processor (The Filter) - Clean floats to integers
    try:
        sale_val = price_info.get("sale_price") or price_info.get("current_price")
        orig_val = price_info.get("price") or price_info.get("original_price")
        discount_val = price_info.get("discount_percentage") or price_info.get("discount_percent") or price_info.get("discount")
        
        sale_price = clean_int(sale_val)
        original_price = clean_int(orig_val)
        discount_percent = clean_int(discount_val)
    except Exception as e:
        logging.warning(f"Error parsing price info: {e}. Falling back to default values.")
        sale_price = 0
        original_price = 0
        discount_percent = 0
        
    saving_amount = original_price - sale_price

    # 2. Strategic Copywriting Array Database (Curated Patterns)
    thai_headline_options = [
        f"หั่นราคาช็อกโลก {discount_percent}%!\nจากปกติ {original_price:_}.- เหลือเพียง {sale_price:_}.-",
        f"ลดจัดหนักวันเดียวเท่านั้น!\nประหยัดเงินในกระเป๋าทันที {saving_amount:_} บาท",
        f"โปรเด็ดไฟไหม้ เหลือแค่ {sale_price:_}.-\nคุ้มกว่านี้ไม่มีอีกแล้ว ของแท้ 100%",
        f"ราคาดิ่งลึกที่สุดในรอบปี!\nจ่ายเพียง {sale_price:_}.- (จากราคาปกติ {original_price:_}.-)"
    ]

    # 3. Secure Random choice
    selected_text = secrets.choice(thai_headline_options)
    return selected_text


def generate_tiktok_3_slides_text(card: dict) -> dict:
    """
    Generates Slide 1 (Hook), Slide 2 (Value), and Slide 3 (CTA) programmatically
    based on the campaign type (source_filename) to strictly enforce the marketing team's guidelines.
    """
    import logging
    campaign = (card.get("source_filename") or "").strip().upper()
    
    def clean_int(val) -> int:
        if val is None:
            return 0
        s = str(val).strip()
        s = s.replace("%", "").strip()
        if not s:
            return 0
        try:
            return int(float(s))
        except ValueError:
            return 0

    price = clean_int(card.get("price"))
    sale_price = clean_int(card.get("sale_price"))
    discount = clean_int(card.get("discount_percentage"))
    item_sold = clean_int(card.get("item_sold") or card.get("sold_count"))
    likes_count = clean_int(card.get("likes_count"))

    # Dynamic calculation if discount is missing but price and sale price are present
    if not discount and price and sale_price and price > sale_price:
        discount = int((price - sale_price) / price * 100)

    # Format numbers with commas (e.g. 1,199)
    price_str = f"{price:,}" if price else "0"
    sale_price_str = f"{sale_price:,}" if sale_price else "0"
    discount_str = str(discount)

    if campaign == 'VOLUME SHOCK':
        slide1 = f"หั่นราคาช็อกโลก {discount_str}%!\nปล่อยหลุดมาได้ยังไง?!"
        slide2 = f"จากปกติ {price_str}.- ตอนนี้เหลือแค่ {sale_price_str}.- เท่านั้น!"
        slide3 = "ระบบจับตาดูอยู่ ราคานี้อยู่ไม่เกิน 2 ชม.\nพิกัดลิงก์หน้าโปรไฟล์!"
    elif campaign == 'MICRO-TRIGGER':
        # Default fallback if sale price is 0
        if sale_price == 0:
            slide1 = "พิกัดของแท้ 1 บาท! มีอยู่จริง ไม่จกตา"
        else:
            slide1 = f"พิกัดของแท้ {sale_price_str} บาท! มีอยู่จริง ไม่จกตา"
            
        # Determine the bank note name based on sale price
        if sale_price <= 10:
            bank_note = "แบงค์สิบ"
        elif sale_price <= 20:
            bank_note = "แบงค์ยี่สิบ"
        elif sale_price <= 50:
            bank_note = "แบงค์ห้าสิบ"
        elif sale_price <= 100:
            bank_note = "แบงค์ร้อย"
        else:
            bank_note = "แบงค์ร้อย"
            
        slide2 = f"{bank_note}มีทอน! เหมาตุนไว้ใช้ได้ทั้งปี"
        slide3 = "กดตุนด่วนก่อนของขาดตลาด\nจิ้มลิงก์หน้าโปรไฟล์เลย!"
    elif campaign == 'GRADE AAA':
        # Format sales volume count
        sales_str = "หมื่น"
        if item_sold > 10000:
            sales_str = f"{int(item_sold/10000):,} หมื่น"
            
        slide1 = f"ตัวดังมหาชน ยอดขายทะลุ{sales_str}!\nรอบนี้ลดราคาลงลึกสุด"
        
        # Format user count based on likes/sales or default to 20,000
        user_count = max(20000, item_sold, likes_count)
        user_count_str = f"{user_count:,}"
        
        slide2 = f"ของแท้ 100% จากแบรนด์ตรง\nการันตีโดยผู้ใช้จริงกว่า {user_count_str} คน"
        slide3 = "คุ้มกว่านี้ไม่มีอีกแล้ว\nเช็คราคาพิเศษที่ลิงก์หน้าโปรไฟล์"
    else:
        # Default fallback (e.g. file.csv or empty)
        slide1 = f"ดีลพิเศษลดแรง {discount_str}%!\nห้ามพลาดเด็ดขาด"
        slide2 = f"จากปกติ {price_str}.- เหลือเพียง {sale_price_str}.-"
        slide3 = "คุ้มกว่านี้ไม่มีอีกแล้ว\nเช็คราคาพิเศษที่ลิงก์หน้าโปรไฟล์"

    return {
        "slide_1_hook": slide1,
        "slide_2_value": slide2,
        "slide_3_cta": slide3
    }



# ---------------------------------------------------------------------------
# Step 1 - Ollama: Generate Script & Prompts (JSON Output)
# ---------------------------------------------------------------------------

def generate_tiktok_caption(card: dict):
    """
    Call local Ollama to create a structured JSON containing:
      - 3 Thai slide copywriting scripts (Hook, Value Comp, CTA)
      - 1 English background vibe description for Slide 1.
    
    Returns:
        (result_json_str: str, error: str | None)
    """
    # -----------------------------------------------------------------------
    # State Purge: Explicitly reset/clear string variables to prevent cache leakage
    # -----------------------------------------------------------------------
    product_anatomy = ""
    vibe_1 = ""
    product_class = ""
    prompt_bg_1 = ""
    prompt_bg_2 = ""
    prompt_bg_3 = ""
    # -----------------------------------------------------------------------

    raw_title = card.get("title") or ""
    raw_desc  = card.get("description") or ""
    title_lower = raw_title.lower()
    
    # Clean infographics before sending to Ollama to prevent them on the background art
    title = clean_product_text(raw_title)
    description = clean_product_text(raw_desc)[:200]
    
    price        = card.get("price") or ""
    sale_price   = card.get("sale_price") or ""
    discount     = card.get("discount_percentage") or ""
    category     = card.get("category") or "ของใช้ทั่วไป"

    # Determine target product category anatomy in English directly from python
    product_anatomy = get_product_anatomy_en(raw_title, category)

    prompt = (
        "คุณคือผู้เชี่ยวชาญด้านการทำ Content TikTok (Copywriter) มีหน้าที่เขียนคำโฆษณาสินค้าแบบ 3 สไลด์\n"
        "ข้อมูลสินค้าที่คุณต้องนำไปเขียนมีดังนี้:\n"
        f"- ชื่อสินค้า: {title}\n"
        f"- ราคาเต็ม: {price} บาท\n"
        f"- ราคาโปรโมชั่น: {sale_price} บาท\n"
        f"- ส่วนลด: {discount}%\n"
        f"- หมวดหมู่: {category}\n"
        f"- รายละเอียด: {description}\n\n"
        "เขียนเนื้อหาสไลด์โฆษณา TikTok 3 หน้า และวิเคราะห์โทนสีแบรนด์และหมวดหมู่เพื่อสร้างคำแนะนำภาษาอังกฤษสำหรับบรรยากาศภาพพื้นหลังแผ่นแรก (Background Vibe) "
        "โดยตอบกลับมาเป็น JSON ในรูปแบบนี้เท่านั้น (ห้ามมีคำพูดเกริ่นนำหรือปิดท้ายนอกเหนือจาก JSON):\n"
        "{\n"
        '  "slide_1_hook": "ข้อความดึงดูดความสนใจยาวไม่เกิน 10 คำสำหรับหน้าแรก",\n'
        '  "slide_2_value": "เปรียบเทียบความคุ้มค่า รายละเอียดสลักราคาลดคุ้มค่าอย่างโดดเด่น",\n'
        '  "slide_3_cta": "ข้อความเชิญชวนให้คนอ่านคลิกดูสินค้าที่ลิงก์หน้าโปรไฟล์",\n'
        '  "vibe_style_1": "English description of the background environment style for Slide 1, e.g. \'elegant calming soft mint gradient, subtle caustic light patterns, white geometric podium\'. STRICT CONSTRAINT: Do not include any product details, product names, or sizes."\n'
        "}\n\n"
        "กฎเกณฑ์ในการตอบกลับ:\n"
        "1. ในคีย์ 'vibe_style_1' ต้องเขียนเป็นภาษาอังกฤษ (English) เสมอ\n"
        "2. ห้ามระบุข้อความแบรนด์, ชื่อสินค้า, หรือลักษณะรูปทรงสินค้าลงใน 'vibe_style_1' เด็ดขาด ให้ระบุเฉพาะบรรยากาศ โทนสี แสง และเอฟเฟกต์แวดล้อมเท่านั้น\n"
        "3. ข้อความภาษาไทยใน slide_1_hook, slide_2_value, slide_3_cta ต้องเขียนกระชับ เหมาะกับหน้า TikTok"
    )

    ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    model      = _get_ollama_model()
    body = {
        "model":  model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
        "options": {
            "temperature": 0.7,
            "num_predict": 1000,
        },
    }
    logging.info(f"[TikTok] Calling local Ollama model={model} to generate scripts for item '{title[:40]}'")

    try:
        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        # Timeout extended as Ollama runs on local CPU and can be slow (set to 3 mins)
        with urllib.request.urlopen(req, timeout=180) as res:
            res_body = json.loads(res.read().decode("utf-8"))
            text = res_body.get("response", "").strip()
            if text:
                logging.info(f"[TikTok] Ollama response successfully received ({len(text)} chars)")
                # Attempt to validate if it is valid JSON
                try:
                    data = json.loads(text)
                    
                    vibe_1 = data.get("vibe_style_1", "A clean studio background with soft lighting.").strip()
                    
                    product_class = product_anatomy
                    
                    # 2. Check if the product category contains apparel/clothing keywords, excluding accessories
                    is_apparel = any(
                        x in category.lower() or x in raw_title.lower() 
                        for x in ["กางเกง", "เสื้อ", "ผ้า", "apparel", "clothing", "fashion", "แฟชั่น", "เครื่องแต่งกาย"]
                    ) and not any(
                        x in raw_title.lower() or x in category.lower()
                        for x in ["ยางรัดผม", "โดนัทรัดผม", "ที่คาดผม", "กิ๊บ", "หมวก", "กระเป๋า", "รองเท้า", "ถุงเท้า", "accessories", "hair tie", "scrunchies", "socks", "bag", "shoes"]
                    )
                    
                    if is_apparel:
                        # Extract a short clothing type term for natural PLACEMENT wording
                        apparel_short = "clothing apparel"
                        if "shorts" in product_class.lower() or "กางเกง" in raw_title.lower():
                            apparel_short = "running shorts"
                        elif "shirt" in product_class.lower() or "เสื้อ" in raw_title.lower():
                            apparel_short = "shirt"
                        elif "suit" in product_class.lower() or "ชุด" in raw_title.lower():
                            apparel_short = "apparel suit"
                            
                        # Slide 1 Prompt (Apparel Category)
                        prompt_bg_1 = (
                            "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                            "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                            "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                            f"[SUBJECT ISOLATION]: Isolate ONLY the main clothing apparel from the center of the reference image. The target subject is: {product_class}. Maintain its exact fabric texture, fabric folds, and athletic cutting shape. "
                            f"PLACEMENT: Instead of a hard podium, floatingly suspend or elegantly display the {apparel_short} at the center of the lower 30% zone, ensuring realistic fabric shadows underneath. "
                            "[BACKGROUND ART ONLY]: Use a clean, soft minimal studio backdrop with a smooth mint green gradient and soft, cinematic diffused lighting to create an airy, breathable, and fresh premium atmosphere."
                        )
                        
                        # Slide 2 Prompt (Apparel Category)
                        prompt_bg_2 = (
                            "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                            "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                            "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                            f"[SUBJECT ISOLATION]: Isolate ONLY the main clothing apparel from the center of the reference image. The target subject is: {product_class}. Maintain its exact fabric texture, fabric folds, and athletic cutting shape. "
                            f"PLACEMENT: Instead of a hard podium, floatingly suspend or elegantly display the {apparel_short} at the center of the lower 30% zone, ensuring realistic fabric shadows underneath. "
                            "[BACKGROUND ART ONLY]: For the surrounding scene, shift the aesthetic to be more dramatic and celebratory. Use an elegant gradient background that infuses subtle, soft golden light particles or ambient light beams reflecting off a clean, polished marble floor."
                        )
                        
                        # Slide 3 Prompt (Apparel Category)
                        prompt_bg_3 = (
                            "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                            "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                            "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                            f"[SUBJECT ISOLATION]: Isolate ONLY the main clothing apparel from the center of the reference image. The target subject is: {product_class}. Maintain its exact fabric texture, fabric folds, and athletic cutting shape. "
                            f"PLACEMENT: Instead of a hard podium, floatingly suspend or elegantly display the {apparel_short} at the center of the lower 30% zone, ensuring realistic fabric shadows underneath. "
                            "[BACKGROUND ART ONLY]: For the surrounding scene, create a cinematic, highly focused atmosphere. The background should feature a deep, soft vignette gradient with high-contrast studio spotlight casting a dramatic, crisp shadow of the product onto the marble floor. The vibe must evoke a sense of a limited-time exhibition or a final closing curtain, creating high visual focus."
                        )
                    else:
                        # Non-Apparel / Packaged Goods
                        is_hardware = any(
                            x in title_lower or x in category.lower()
                            for x in ["sensor", "night light", "puck light", "ไฟเซ็นเซอร์", "โคมไฟ", "electronics", "อุปกรณ์"]
                        )
                        
                        if is_hardware:
                            product_class = "A sleek, minimal white circular motion-sensor puck light, showing its smooth frosted plastic diffuser front and modern round chassis design."
                            product_class = clean_state(product_class)
                            
                            prompt_bg_1 = (
                                "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                                "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                                "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                                f"[SUBJECT ISOLATION]: Isolate ONLY the main product from the reference image. The target subject is: {product_class}. Maintain its exact shape, colors, and textures on the podium. Do not morph it. "
                                f"PLACEMENT: Place this isolated {product_class} firmly on top of a single, central, monolithic white geometric podium positioned in the lower portion of the frame. Ensure high-fidelity contact shadows underneath. "
                                "[BACKGROUND ART ONLY]: For the surrounding backdrop, use an elegant calming soft mint green color gradient with subtle caustic light patterns on a polished floor."
                            )
                            
                            # Slide 2 Prompt: Restructured String Concatenation exactly as specified by user
                            prompt_bg_2 = (
                                "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                                "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                                "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                                "[SUBJECT ISOLATION]: Isolate ONLY the main product from the reference image. The target subject is: " + product_class + ". Maintain its exact white circular puck shape, electronic plastic casing, and smooth rounded textures on the podium. Do not morph it into any pouch, sachet, or skincare bottle. "
                                "PLACEMENT: Place this isolated " + product_class + " firmly on top of a single, central, monolithic white geometric podium positioned in the lower portion of the frame. "
                                "[BACKGROUND ART ONLY]: For the surrounding scene, apply the warm and celebratory vibe of the Volume Shock campaign. Use an elegant gradient backdrop that infuses subtle, soft golden light particles and warm premium ambient light beams reflecting off a clean, polished marble floor."
                            )
                            
                            prompt_bg_3 = (
                                "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                                "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                                "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                                f"[SUBJECT ISOLATION]: Isolate ONLY the main product from the reference image. The target subject is: {product_class}. Maintain its exact shape, colors, and textures on the podium. Do not morph it. "
                                f"PLACEMENT: Place this isolated {product_class} firmly on top of a single, central, monolithic white geometric podium positioned in the lower portion of the frame. Ensure high-fidelity contact shadows underneath. "
                                "[BACKGROUND ART ONLY]: For the surrounding scene, create a cinematic, highly focused atmosphere. The background should feature a deep, soft vignette gradient with high-contrast studio spotlight casting a dramatic, crisp shadow of the product onto the marble floor. The vibe must evoke a sense of a limited-time exhibition or a final closing curtain, creating high visual focus."
                            )
                        else:
                            # Determine Slide 2 subject isolation details dynamically to prevent hardcoding leaks
                            if any(x in title_lower for x in ["skintific", "cushion", "คุชชั่น"]):
                                subject_isolation_details = "Maintain its exact round shape, metallic gold surface texture, and luxurious design on the podium. Do not morph it into a pouch or a bottle."
                            elif any(x in title_lower for x in ["dd cream", "ดีดีครีม", "watermelon", "แตงโม", "jula"]):
                                subject_isolation_details = "Maintain its exact rectangular sachet pouch shape, red-pink watermelon branding colors, and top cap texture on the podium. Do not morph it into a tube or a bottle."
                            elif any(x in title_lower for x in ["innerdeo", "persimmon", "ลดกลิ่นกาย"]):
                                subject_isolation_details = "Maintain its exact cylindrical medicine pill bottle jar shape, white cap, and clean label design on the podium. Do not morph it into a pump lotion bottle or a cosmetic tube."
                            elif any(x in title_lower for x in ["gluta-hya", "กลูต้า-ไฮยา", "tube", "หลอด"]):
                                subject_isolation_details = "Maintain its exact flat squeeze tube shape, upside-down cap positioning, and specific product variant color (e.g., pink Dewy Radiance or blue Overnight Repair) firmly on the podium. Do not morph it into a cylinder bottle or add a pump dispenser head."
                            else:
                                subject_isolation_details = "Maintain its exact shape, colors, and textures on the podium. Do not morph it."

                            prompt_bg_1 = (
                                "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                                "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                                "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                                f"[SUBJECT ISOLATION]: Isolate ONLY the main product from the reference image. The target subject is: {product_class}. Maintain its exact shape, colors, and textures on the podium. Do not morph it. "
                                f"PLACEMENT: Place this isolated {product_class} firmly on top of a single, central, monolithic white geometric podium positioned in the lower portion of the frame. Ensure high-fidelity contact shadows underneath. "
                                "[BACKGROUND ART ONLY]: For the surrounding backdrop, use an elegant calming soft mint green color gradient with subtle caustic light patterns on a polished floor."
                            )
                            
                            # Refined Concatenation Logic for Slide 2 based on the marketing guidelines
                            if any(x in title_lower for x in ["gluta-hya", "กลูต้า-ไฮยา", "tube", "หลอด"]):
                                prompt_bg_2 = (
                                    "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                                    "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                                    "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                                    "[SUBJECT ISOLATION]: Isolate ONLY the main product from the reference image. The dynamic target subject is: " + product_class + ". " + subject_isolation_details + " "
                                    "PLACEMENT: Place this isolated " + product_class + " firmly on top of a single, central, monolithic white geometric podium positioned in the lower portion of the frame. Ensure high-fidelity contact shadows underneath. "
                                    "[BACKGROUND ART ONLY]: For the surrounding scene, amplify the celebratory feel of the Volume Shock campaign. Use an elegant gradient background that infuses subtle, soft golden light particles or ambient light beams reflecting off a clean, polished marble floor."
                                )
                            else:
                                prompt_bg_2 = (
                                    "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                                    "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                                    "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                                    f"[SUBJECT ISOLATION]: Isolate ONLY the main product from the reference image. The target subject is: {product_class}. {subject_isolation_details} "
                                    f"PLACEMENT: Place this isolated {product_class} firmly on top of a single central white geometric podium positioned in the lower portion of the frame. "
                                    "[BACKGROUND ART ONLY]: For the surrounding scene, amplify the celebratory and high-value feel of the Volume Shock campaign. Use an elegant gradient backdrop that infuses subtle, soft golden light particles and warm premium ambient light beams reflecting off a clean, polished marble floor."
                                )
                            
                            prompt_bg_3 = (
                                "Strictly generate this image in a vertical 9:16 aspect ratio for mobile fullscreen displays. "
                                "Spatial Rule (60/30/10): The top 60% MUST be completely empty, blank, clean gradient negative space for text layout. The middle-bottom 30% is the active product zone. The absolute bottom 10% is a safe margin area. "
                                "Constraint: Strictly exclude any written text, characters, numbers, or brand logos on the background art. "
                                f"[SUBJECT ISOLATION]: Isolate ONLY the main product from the reference image. The target subject is: {product_class}. Maintain its exact shape, colors, and textures on the podium. Do not morph it. "
                                f"PLACEMENT: Place this isolated {product_class} firmly on top of a single, central, monolithic white geometric podium positioned in the lower portion of the frame. Ensure high-fidelity contact shadows underneath. "
                                "[BACKGROUND ART ONLY]: For the surrounding scene, create a cinematic, highly focused atmosphere. The background should feature a deep, soft vignette gradient with high-contrast studio spotlight casting a dramatic, crisp shadow of the product onto the marble floor. The vibe must evoke a sense of a limited-time exhibition or a final closing curtain, creating high visual focus."
                            )
                    
                    # Generate slide texts based on the marketing team's 3-Slide Formula
                    slides_text = generate_tiktok_3_slides_text(card)
                    
                    # Construct clean response JSON structure
                    result_data = {
                        "slide_1_hook": slides_text["slide_1_hook"],
                        "slide_2_value": slides_text["slide_2_value"],
                        "slide_3_cta": slides_text["slide_3_cta"],
                        "prompt_bg_1": clean_state(prompt_bg_1),
                        "prompt_bg_2": clean_state(prompt_bg_2),
                        "prompt_bg_3": clean_state(prompt_bg_3)
                    }
                    
                    return json.dumps(result_data, ensure_ascii=False), None
                except Exception as je:
                    logging.warning(f"[TikTok] Ollama response was not valid JSON, returning raw text: {je}")
                    return text, f"Response was not valid JSON: {je}"
            return None, "Ollama returned empty response"
    except Exception as exc:
        logging.error(f"[TikTok] Ollama error: {exc}")
        return None, f"Ollama error: {exc}"


# ---------------------------------------------------------------------------
# Step 2 - Pillow Programmatic Image Composition
# ---------------------------------------------------------------------------

def parse_line_segments(line: str, ghost_str: str, promo_str: str) -> list:
    """
    Parses a line of text into segments with styles: 'primary', 'ghost', 'promo'.
    Allows applying specific styling/colors to individual parts of a line.
    """
    segments = []
    current_idx = 0
    matches = []
    
    if ghost_str and ghost_str in line:
        idx = line.find(ghost_str)
        matches.append((idx, idx + len(ghost_str), 'ghost'))
        
    if promo_str and promo_str in line:
        idx = line.find(promo_str)
        overlap = False
        for m in matches:
            if not (idx + len(promo_str) <= m[0] or idx >= m[1]):
                overlap = True
                break
        if not overlap:
            matches.append((idx, idx + len(promo_str), 'promo'))
            
    # Sort matches by start index
    matches.sort(key=lambda x: x[0])
    
    for start, end, style in matches:
        if start > current_idx:
            segments.append((line[current_idx:start], 'primary'))
        segments.append((line[start:end], style))
        current_idx = end
        
    if current_idx < len(line):
        segments.append((line[current_idx:], 'primary'))
        
    if not segments:
        segments.append((line, 'primary'))
        
    return segments


def draw_single_line_with_shadow(draw, bg_img, text, font, fill, y):
    """Draw a single line of centered text with a professional, soft drop shadow."""
    w = draw.textlength(text, font=font)
    x = (1080 - w) / 2
    
    # 1. Render Drop Shadow
    shadow_img = Image.new("RGBA", bg_img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_draw.text((x, y + 5), text, font=font, fill=(0, 0, 0, 102))
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=10))
    bg_img.alpha_composite(shadow_img)
    
    # 2. Render Main Text
    draw.text((x, y), text, font=font, fill=fill)


def draw_text_wrapped(
    draw, text, font, fill, max_width, start_y, line_spacing=1.4,
    stroke_fill=None, stroke_width=0,
    ghost_price_str=None, promo_price_str=None,
    color_primary=(30, 41, 59, 255),
    color_promo=(220, 38, 38, 255),
    color_ghost=(148, 163, 184, 255),
    bg_img=None
):
    """Draw text and wrap lines automatically, supporting segment-based coloring, strikethroughs, and drop shadows."""
    text = text.replace('\r', '')
    lines = []
    current_line = ""
    for token in text:
        if token == '\n':
            lines.append(current_line)
            current_line = ""
            continue
        test_line = current_line + token
        w = draw.textlength(test_line, font=font)
        if w > max_width and current_line:
            lines.append(current_line)
            current_line = token
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)

    y = start_y
    font_height = font.size
    for line in lines:
        segments = parse_line_segments(line, ghost_price_str, promo_price_str)
        
        # Calculate total width of all segments
        total_w = 0
        for segment_text, style in segments:
            total_w += draw.textlength(segment_text, font=font)
            
        # Center horizontally
        x_start = (1080 - total_w) / 2
        
        # 1. Render Drop Shadows for all segments first
        if bg_img:
            shadow_img = Image.new("RGBA", bg_img.size, (0, 0, 0, 0))
            shadow_draw = ImageDraw.Draw(shadow_img)
            x_shadow = x_start
            for segment_text, style in segments:
                shadow_draw.text((x_shadow, y + 4), segment_text, font=font, fill=(0, 0, 0, 89))
                x_shadow += draw.textlength(segment_text, font=font)
            shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=10))
            bg_img.alpha_composite(shadow_img)
            
        # 2. Render Main Text segments
        x_text = x_start
        for segment_text, style in segments:
            # Determine color/fill
            if style == 'ghost':
                fill_color = color_ghost
            elif style == 'promo':
                fill_color = color_promo
            else:
                fill_color = fill
                
            # Draw segment
            if stroke_fill and stroke_width > 0:
                draw.text((x_text, y), segment_text, font=font, fill=fill_color, stroke_width=stroke_width, stroke_fill=stroke_fill)
            else:
                draw.text((x_text, y), segment_text, font=font, fill=fill_color)
                
            w = draw.textlength(segment_text, font=font)
            
            # If style is ghost, draw a central horizontal strikethrough line ONLY over this segment
            if style == 'ghost':
                strike_y = y + int(font_height / 2) + 2
                # Drop shadow for strikethrough line
                if bg_img:
                    shadow_img = Image.new("RGBA", bg_img.size, (0, 0, 0, 0))
                    shadow_draw = ImageDraw.Draw(shadow_img)
                    shadow_draw.line([(x_text - 2, strike_y + 4), (x_text + w + 2, strike_y + 4)], fill=(0, 0, 0, 89), width=4)
                    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=10))
                    bg_img.alpha_composite(shadow_img)
                # Main strikethrough line
                draw.line([(x_text - 2, strike_y), (x_text + w + 2, strike_y)], fill=color_ghost, width=4)
                
            x_text += w
            
        y += int(font_height * line_spacing)
    return y


def clean_currency_text(text: str) -> str:
    """
    Strips raw currency symbols like '฿' from the text,
    and transforms strings like '฿299.-' or '฿518' into '299.-' or '518.-'.
    """
    if not text:
        return ""
    import re
    cleaned = re.sub(r'฿\s*(\d+(?:[.,]\d+)*)(?:\.-)?', r'\1.-', text)
    cleaned = cleaned.replace('฿', '')
    cleaned = cleaned.replace('.-.-', '.-')
    return cleaned


def compose_tiktok_slide_image(bg_image_path, product_image_url, text_content, output_path, slide_num, price_info=None):
    """
    Programmatically composes a 9:16 TikTok story image.
    
    1. Opens the background image (1080x1920 recommended, resized if not).
    2. Downloads and overlays the product image in the bottom half (ONLY on fallback background).
    3. Renders the Thai text in the top 60% area with Prompt-Bold & Prompt-Regular fonts,
       perfectly centering the text block vertically and horizontally.
    4. Saves the finished composition.
    """
    logging.info(f"[Composition] Processing slide {slide_num} -> {output_path}")
    
    canvas_w = 1080
    canvas_h = 1920
    is_fallback_bg = False

    # 1. Load Background Image
    if not bg_image_path or not os.path.exists(bg_image_path):
        is_fallback_bg = True
        # Create a default premium light gradient background if no upload exists (Slate 50 to Slate 200)
        bg_img = Image.new("RGBA", (canvas_w, canvas_h), (248, 250, 252, 255))
        draw = ImageDraw.Draw(bg_img)
        # Render a subtle clean light-grey vertical gradient
        for y in range(canvas_h):
            r = int(248 - (y / canvas_h) * 20)
            g = int(250 - (y / canvas_h) * 18)
            b = int(252 - (y / canvas_h) * 12)
            draw.line([(0, y), (canvas_w, y)], fill=(r, g, b, 255))
    else:
        try:
            bg_img = Image.open(bg_image_path).convert("RGBA")
            # Resize/crop to exactly 1080x1920
            if bg_img.size != (canvas_w, canvas_h):
                bg_img = bg_img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
        except Exception as e:
            logging.error(f"[Composition] Failed to load background: {e}")
            # Create light gradient as fallback
            bg_img = Image.new("RGBA", (canvas_w, canvas_h), (248, 250, 252, 255))
            draw = ImageDraw.Draw(bg_img)
            for y in range(canvas_h):
                r = int(248 - (y / canvas_h) * 20)
                g = int(250 - (y / canvas_h) * 18)
                b = int(252 - (y / canvas_h) * 12)
                draw.line([(0, y), (canvas_w, y)], fill=(r, g, b, 255))
            is_fallback_bg = True

    # Create overlay drawing context
    draw = ImageDraw.Draw(bg_img)

    # Load Fonts (placed in the same folder)
    base_dir = os.path.dirname(__file__)
    font_regular_path = os.path.join(base_dir, "Prompt-Regular.ttf")
    font_bold_path = os.path.join(base_dir, "Prompt-Bold.ttf")

    # Fallback to system default if fonts not present
    if os.path.exists(font_bold_path) and os.path.exists(font_regular_path):
        font_title = ImageFont.truetype(font_bold_path, 60)
        font_body = ImageFont.truetype(font_regular_path, 46)
        font_badge = ImageFont.truetype(font_bold_path, 36)
    else:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_badge = ImageFont.load_default()

    # Clean the input text and prep segments
    cleaned_text = text_content.strip()
    if cleaned_text.startswith("Slide") and ":" in cleaned_text:
        cleaned_text = cleaned_text.split(":", 1)[1].strip()

    cleaned_text = clean_currency_text(cleaned_text)

    # 1. Determine Backdrop Luminance & Default Text Colors
    # Calculate average luminance of the text area (top 60% of the canvas: 0 to 1152px)
    text_area = bg_img.crop((0, 0, canvas_w, int(canvas_h * 0.6)))
    stat = ImageStat.Stat(text_area.convert("L"))
    mean_luminance = stat.mean[0] # value between 0 and 255
    
    if mean_luminance < 128:
        # Dark background -> use White text
        text_color = (255, 255, 255, 255)
        color_ghost = (203, 213, 225, 255) # Light gray
    else:
        # Light background -> use Dark text
        text_color = (30, 41, 59, 255) # Charcoal Black
        color_ghost = (148, 163, 184, 255) # Muted Slate Gray

    # Enforce Slide 2 Contrast Inversion: change Line 1 color from black to solid White (#FFFFFF)
    if slide_num == 2:
        text_color = (255, 255, 255, 255)
        color_ghost = (203, 213, 225, 255)

    # Wrap main text into lines to measure height
    max_text_width = 920 # Margin of 80px on each side
    
    # Font settings & Slide 1 scale up
    if slide_num == 1:
        font_bold_75 = ImageFont.truetype(font_bold_path, 75) if os.path.exists(font_bold_path) else ImageFont.load_default()
        font_regular_45 = ImageFont.truetype(font_regular_path, 45) if os.path.exists(font_regular_path) else ImageFont.load_default()
        
        lines = [line.strip() for line in cleaned_text.split('\n') if line.strip()]
        line_heights = []
        for i, line in enumerate(lines):
            f = font_bold_75 if i == 0 else font_regular_45
            line_heights.append(int(f.size * 1.4))
        body_height = sum(line_heights)
    else:
        body_lines = []
        current_line = ""
        for token in cleaned_text:
            if token == '\n':
                body_lines.append(current_line)
                current_line = ""
                continue
            test_line = current_line + token
            w = draw.textlength(test_line, font=font_title)
            if w > max_text_width and current_line:
                body_lines.append(current_line)
                current_line = token
            else:
                current_line = test_line
        if current_line:
            body_lines.append(current_line)
        line_h = int(font_title.size * 1.4)
        body_height = len(body_lines) * line_h

    # Calculate height for centering within top 60% clear space (0 to 1152px)
    total_height = 0
    badge_height = 0
    badge_margin = 0
    total_height += badge_height + badge_margin
    total_height += body_height

    draw_price_overlay = False
    overlay_margin = 60
    promo_margin = 20
    orig_h = font_body.size

    # Slide 2: Format the discount line scale up to 90px (Extra Bold)
    if slide_num == 2 and price_info:
        # Check if the main text already contains price keywords (to prevent double rendering)
        has_price_in_text = any(x in cleaned_text for x in ["เหลือเพียง", "ปกติ", "ประหยัด", "จ่ายเพียง", "ลดจัดหนัก"])
        if not has_price_in_text:
            draw_price_overlay = True
            font_promo_90 = ImageFont.truetype(font_bold_path, 90) if os.path.exists(font_bold_path) else ImageFont.load_default()
            promo_h = font_promo_90.size
            total_height += overlay_margin + promo_h + promo_margin + orig_h
        else:
            promo_h = font_title.size
    else:
        promo_h = font_title.size

        # Centering zone: enforce top padding buffer (12-15% of canvas height)
    top_padding_buffer = int(canvas_h * 0.13)  # ~13% of height (~250px)
    max_text_area_h = int(canvas_h * 0.6)  # top 60% reserved for text
    available_height = max_text_area_h - top_padding_buffer
    if total_height < available_height:
        start_y = top_padding_buffer + (available_height - total_height) // 2
    else:
        start_y = top_padding_buffer

    logging.info(f"[Composition] Calculated layout total_height: {total_height}px, start_y: {start_y}px")

# Slide badge removed per requirement: no SLIDE X / 3 indicator.
    # Render "SLIDE X / 3" as a naked, clean, minimalist string using light gray text (#CBD5E1) directly onto the backdrop.


    badge_y = start_y

    
    current_y = badge_y + badge_height + badge_margin

    # Find ghost and promo price strings in price_info to pass for inline styling
    ghost_price_str = None
    promo_price_str = None
    if price_info:
        orig_p = price_info.get("price")
        sale_p = price_info.get("sale_price")
        if orig_p:
            try:
                op_int = int(float(orig_p))
                for p_str in [f"{op_int:,}.-", f"{op_int}.-", f"{op_int:,}", f"{op_int}"]:
                    if p_str in cleaned_text:
                        ghost_price_str = p_str
                        break
            except Exception:
                pass
        if sale_p:
            try:
                sp_int = int(float(sale_p))
                for p_str in [f"{sp_int:,}.-", f"{sp_int}.-", f"{sp_int:,}", f"{sp_int}"]:
                    if p_str in cleaned_text:
                        promo_price_str = p_str
                        break
            except Exception:
                pass

    # Draw body lines
    if slide_num == 1:
        # Slide 1 Typography Scale Up: Line 1 -> 75px Bold, Line 2 -> 45px Medium (Regular)
        for i, line in enumerate(lines):
            f = font_bold_75 if i == 0 else font_regular_45
            w = draw.textlength(line, font=f)
            draw.text(((canvas_w - w) / 2, current_y), line, font=f, fill=text_color)
            current_y += int(f.size * 1.4)
    else:
        current_y = draw_text_wrapped(
            draw, cleaned_text, font_title, text_color,
            max_text_width, current_y, line_spacing=1.5,
            stroke_fill=None, stroke_width=0,
            ghost_price_str=ghost_price_str,
            promo_price_str=promo_price_str,
            color_primary=text_color,
            color_promo=(220, 38, 38, 255),  # Ruby Crimson Red (#DC2626)
            color_ghost=color_ghost,
            bg_img=bg_img
        )

    # 3. Draw Price Tag Overlay (if applicable)
    if draw_price_overlay:
        try:
            discount = int(float(price_info.get("discount_percentage") or 0))
            price = int(float(price_info.get("price") or 0))
            sale_price = int(float(price_info.get("sale_price") or 0))
        except Exception:
            discount = price_info.get("discount_percentage")
            price = price_info.get("price")
            sale_price = price_info.get("sale_price")
            
        price_tag_y = current_y + overlay_margin
        
        # Promo price text
        price_text = f"ลด {discount}% เหลือเพียง {sale_price:_}.-"
        font_promo = ImageFont.truetype(font_bold_path, 90) if os.path.exists(font_bold_path) else ImageFont.load_default()
        
        # Draw promo price with drop shadow
        draw_single_line_with_shadow(draw, bg_img, price_text, font_promo, (220, 38, 38, 255), price_tag_y)
        
        # Original price subtext
        prefix_text = "ปกติ "
        price_val_text = f"{price:_}.-"
        
        prefix_w = draw.textlength(prefix_text, font=font_body)
        price_w = draw.textlength(price_val_text, font=font_body)
        total_w = prefix_w + price_w
        start_x = (canvas_w - total_w) / 2
        
        orig_y = price_tag_y + font_promo.size + promo_margin
        strikethrough_y = orig_y + int(font_body.size / 2) + 2
        
        # Draw drop shadow for original price prefix, value, and strikethrough line
        shadow_img = Image.new("RGBA", bg_img.size, (0, 0, 0, 0))
        shadow_draw = ImageDraw.Draw(shadow_img)
        shadow_draw.text((start_x, orig_y + 4), prefix_text, font=font_body, fill=(0, 0, 0, 89))
        shadow_draw.text((start_x + prefix_w, orig_y + 4), price_val_text, font=font_body, fill=(0, 0, 0, 89))
        shadow_draw.line(
            [(start_x + prefix_w - 4, strikethrough_y + 4), (start_x + total_w + 4, strikethrough_y + 4)], 
            fill=(0, 0, 0, 89), 
            width=4
        )
        shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=10))
        bg_img.alpha_composite(shadow_img)

        # Draw main text for original price
        draw.text((start_x, orig_y), prefix_text, font=font_body, fill=color_ghost)
        draw.text((start_x + prefix_w, orig_y), price_val_text, font=font_body, fill=color_ghost)
        draw.line(
            [(start_x + prefix_w - 4, strikethrough_y), (start_x + total_w + 4, strikethrough_y)], 
            fill=color_ghost, 
            width=4
        )

    # 4. Download and Overlay Product Image (Bottom Center Area - ONLY for fallback backgrounds)
    if product_image_url and is_fallback_bg:
        prod_img_path = None
        try:
            # Simple local cache for product images based on hash
            import hashlib
            url_hash = hashlib.md5(product_image_url.encode('utf-8')).hexdigest()
            temp_dir = os.path.join(base_dir, "static", "uploads")
            os.makedirs(temp_dir, exist_ok=True)
            prod_img_path = os.path.join(temp_dir, f"prod_temp_{url_hash}.png")

            if not os.path.exists(prod_img_path):
                # Download product image
                req = urllib.request.Request(product_image_url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=30) as response:
                    with open(prod_img_path, 'wb') as out_file:
                        out_file.write(response.read())

            if os.path.exists(prod_img_path):
                prod_img = Image.open(prod_img_path).convert("RGBA")
                
                # Make the product image fit nicely in a square card (e.g. 500x500 max)
                max_size = 520
                prod_img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
                
                # Create a rounded border card for the product to stand out on dark/light backgrounds
                pw, ph = prod_img.size
                card_padding = 24
                cx1 = (canvas_w - pw) / 2 - card_padding
                cy1 = 1400 - (ph / 2) - card_padding
                cx2 = (canvas_w + pw) / 2 + card_padding
                cy2 = 1400 + (ph / 2) + card_padding

                # Render background card with shadow
                draw.rounded_rectangle(
                    [(cx1, cy1), (cx2, cy2)],
                    radius=32,
                    fill=(255, 255, 255, 240), # Solid clean white card
                    outline=(229, 231, 235, 255), # Grey border
                    width=2
                )
                
                # Composite product image onto the white card
                paste_x = int((canvas_w - pw) / 2)
                paste_y = int(1400 - (ph / 2))
                bg_img.alpha_composite(prod_img, (paste_x, paste_y))
                
                logging.info(f"[Composition] Successfully overlaid product image for slide {slide_num}")
        except Exception as e:
            logging.error(f"[Composition] Failed to download or overlay product image: {e}")

    # 5. Save Finished Canvas
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    # Save as PNG
    bg_img.convert("RGB").save(output_path, "JPEG", quality=95)
    logging.info(f"[Composition] Saved finished slide: {output_path}")
