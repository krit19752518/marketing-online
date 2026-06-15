import os
import json
import urllib.request
import sqlite3
import random

def get_gemini_api_keys():
    keys_str = os.getenv("GEMINI_API_KEYS")
    if keys_str:
        return [k.strip() for k in keys_str.split(",") if k.strip()]
    single_key = os.getenv("GEMINI_API_KEY")
    if single_key:
        return [single_key]
    return ["AIzaSyBNb6oiwC_hmECeGq1JegH6qJm4SyWR9MU"]

def get_openrouter_api_key():
    key = os.getenv("OPENROUTER_API_KEY")
    if key:
        return key
    try:
        cred_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "openrouter_cred.json")
        if os.path.exists(cred_path):
            with open(cred_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    return data[0].get("data", {}).get("apiKey")
    except Exception as e:
        print(f"Error reading openrouter_cred.json: {e}")
    return None

def get_ollama_model():
    ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
    try:
        url = f"{ollama_url}/api/tags"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as res:
            data = json.loads(res.read().decode('utf-8'))
            models = [m['name'] for m in data.get('models', [])]
            for m in ['llama3.2:3b', 'llama3.2', 'llama3']:
                if m in models:
                    return m
            if models:
                return models[0]
    except Exception:
        pass
    return "llama3.2:3b"


def generate_shopee_caption(card):
    title = card.get('title') or ""
    description = card.get('description') or ""
    price = card.get('price')
    sale_price = card.get('sale_price')
    discount = card.get('discount_percentage')
    link = card.get('product_short_link') or card.get('product_link') or ""
    image = card.get('image_link') or ""
    rating = card.get('item_rating')
    sold = card.get('item_sold')
    source_filename = card.get('source_filename') or ""

    # Define variations lists for GRADE AAA
    aaa_headers = [
        "🟢 **RADAR SIGNAL: GRADE AAA - สัญญาณซื้อด่วน !**",
        "🟢 **PRICE RADAR: GRADE AAA - ดิ่งลึกแนวรับ ทุบราคาด่วน !**",
        "🟢 **RADAR SIGNAL: GRADE AAA - จุดสะสมของถูกระดับพรีเมียม !**",
        "🟢 **PRICE RADAR: GRADE AAA - ดีลเด็ดราคาหลุดแนวต้าน !**",
        "🟢 **RADAR SIGNAL: GRADE AAA - สัญญาณราคาหลุดแนวรับสำคัญ !**",
        "🟢 **PRICE RADAR: GRADE AAA - ดีลเกรด AAA ราคาลงต่ำสุดรอบสัปดาห์ !**"
    ]
    aaa_intros = [
        "ระบบเรดาร์หลังบ้านตรวจพบสินค้า 'ของมันต้องมี' ที่ผ่านเกณฑ์ความปลอดภัยขั้นสุด! คัดมาเฉพาะร้านแท้ชัวร์ (Official Mall) ที่คนซื้อจริงรีวิวให้ทะลุ 4.8 ดาว แถมตอนนี้ราคาถูกทุบดิ่งลงมาต่ำกว่าเส้นค่าเฉลี่ยซะจนต้องขยี้ตา!",
        "ระบบสแกนราคากลางตรวจพบดีลระดับพรีเมียม 5 ดาวโดนเจ้ามือทุบดิ่งลงมาลึกมาก! คัดมาเฉพาะร้านแท้ Official Mall ที่ประวัติยอดขายดีเยี่ยมและรับประกันความปลอดภัยของเงินในกระเป๋า!",
        "เรดาร์หลังบ้านจับซิกแนลสินค้าแบรนด์ดังที่ราคาหลุดทะลุขอบล่างของเส้นค่าเฉลี่ย! คัดเฉพาะร้านแท้ Official ที่รีวิวล้นหลาม ปลอดภัยไม่เสี่ยงดอยชัวร์!",
        "ระบบเรดาร์ตรวจจับพฤติกรรมราคาพบว่าสินค้าตัวท็อปกำลังเผชิญแรงขายลดราคาจนทะลุจุดต่ำสุดเดิม! เป็นร้านค้าทางการยอดขายสูง รีวิวแน่น การันตีความปลอดภัยสูงมาก!",
        "ระบบหลังบ้านแจ้งเตือนสินค้าขายดีระดับ 5 ดาวเกิดการตัดราคาแบบไม่คาดฝัน! คัดเฉพาะร้านทางการ Official Mall เท่านั้น มั่นใจได้ของแท้ไม่มีดรอป!"
    ]
    aaa_connectors = [
        "นี่ไม่ใช่แค่ของถูก แต่คือ 'จุดเข้าซื้อที่ปลอดภัยที่สุด' ในตลาดตอนนี้:",
        "จังหวะนี้คือจุดเข้าสะสมของที่ปลอดภัยที่สุดในรอบสัปดาห์ครับ:",
        "จุดซื้อที่ปลอดภัยที่สุดในตลาดตอนนี้เปิดแล้วครับพี่น้อง:",
        "รอบนี้บอกเลยว่าความเสี่ยงต่ำสุดๆ ดีลนี้เข้าซื้อได้ปลอดภัยแน่นอน:",
        "คัดกรองมาให้เป็นจุดเข้าซื้อที่คุ้มค่าและไร้ความเสี่ยงที่สุด ณ เวลานี้:"
    ]
    aaa_fallbacks = [
        f"กราฟราคาดิ่งลงแบบนี้ หลุดแนวรับไปแล้ว ได้ส่วนลดถึง {discount or '0'}% รีบกดไว้ก่อนที่ราคาจะขึ้นนะครับ",
        f"เจ้ามือทุบราคาเคลียร์ทางขนาดนี้ ได้ส่วนลด {discount or '0'}% จังหวะช้อนด่วนๆ เลยครับ!",
        f"ราคาม้วนหัวลงมาลึกมาก ได้ส่วนลดตั้ง {discount or '0'}% รีบกดก่อนกราฟจะเด้งกลับนะ!",
        f"ราคานี้หาไม่ได้บ่อยๆ ลดไปถึง {discount or '0'}% โอกาสเข้าซื้อที่คุ้มที่สุดในสัปดาห์นี้เลยครับ",
        f"ดึงราคาลงต่ำกว่าปกติเยอะมาก ได้ส่วนลด {discount or '0'}% รีบเก็บเข้าพอร์ตด่วนเลยครับ",
        f"กราฟราคาหัวทิ่มลงแรงแบบนี้ ได้ส่วนลดถึง {discount or '0'}% แย่งกดให้ทันก่อนราคาจะปรับขึ้นนะครับ"
    ]

    # Define variations lists for VOLUME SHOCK
    vs_headers = [
        "🔴 **RADAR SIGNAL: VOLUME SHOCK - ตลาดเทขาย เคลียร์สต็อกด่วน !**",
        "🔴 **PRICE RADAR: VOLUME SHOCK - ดีลล้างสต็อกโวลุ่มทะลักด่วน !**",
        "🔴 **RADAR SIGNAL: VOLUME SHOCK - ร้านค้าเทขายพอร์ตหมดแล้วหมดเลย !**",
        "🔴 **PRICE RADAR: VOLUME SHOCK - โวลุ่มถล่มทลาย ราคาถูกทุบเคลียร์คลัง !**",
        "🔴 **RADAR SIGNAL: VOLUME SHOCK - สัญญาณเทกระจาดล้างสต็อกครั้งใหญ่ !**"
    ]
    vs_intros = [
        "ระบบเรดาร์หลังบ้านตรวจพบสินค้าลดราคาล้างสต็อกที่มีแรงซื้อหนาแน่นผิดปกติ! คัดมาเฉพาะร้านแท้ชัวร์ (Official Mall) ที่คนแห่ช็อปจนโวลุ่มทะลักทลาย และตอนนี้ราคาโดนทุบดิ่งเคลียร์สต็อกหมดแล้วหมดเลย!",
        "เรดาร์หลังบ้านตรวจพบสินค้าโวลุ่มถล่มทลาย ร้านค้าพากันดัมพ์ราคาล้างสต็อกด่วน! คัดเฉพาะร้านแท้ Official Mall ที่มีรีวิวแน่นๆ การันตีซื้อแล้วปลอดภัยแน่นอน!",
        "ระบบตรวจจับปริมาณการซื้อขายจับสัญญาณการลดล้างพอร์ตครั้งใหญ่ของร้านค้าทางการ! ราคาถูกทุบเคลียร์สต็อกแบบไม่เอาไรเลย ช็อปด่วนก่อนของเกลี้ยง!",
        "สัญญาณโวลุ่มกระฉูดสะท้อนแรงเทขายล้างสต็อกของร้านค้าใหญ่! คัดมาเฉพาะดีล 5 ดาวจากร้านแท้ชัวร์ รีวิวเพียบ ช็อปหนีความเสี่ยงได้เลย!",
        "เรดาร์หลังบ้านตรวจพบบัญชีร้านค้าทางการตัดใจดัมพ์ราคาล้างสต็อกระบายสินค้าด่วนที่สุด! ของแท้ชัวร์ มั่นใจ ปลอดภัยแน่นอน!"
    ]
    vs_connectors = [
        "นี่คือจังหวะที่ร้านค้าเทขายล้างพอร์ตที่คุ้มค่าที่สุดในตลาดตอนนี้:",
        "โอกาสทองของคนเฝ้าจอ ดีลล้างพอร์ตแบบคุ้มค่าที่สุดเวลานี้:",
        "จุดเข้าซื้อล้างสต็อกที่ราคาดีที่สุดในรอบสัปดาห์:",
        "โวลุ่มแรงแบบนี้ โอกาสช็อปของถูกที่สุดเปิดแล้วครับ:",
        "ลดเคลียร์สต็อกแบบนี้ จุดซื้อที่ดีที่สุดอยู่ในมือคุณแล้ว:"
    ]
    vs_fallbacks = [
        f"กราฟราคาดิ่งลงแบบนี้ หลุดแนวรับไปแล้ว ได้ส่วนลดถึง {discount or '0'}% รีบกดไว้ก่อนที่สินค้าจะหมดสต็อกนะครับ",
        f"โวลุ่มขายถล่มทลายล้างสต็อกลดถึง {discount or '0'}% รีบเก็บเข้ากระเป๋าก่อนสต็อกหมดเลยครับ!",
        f"ลดเคลียร์สต็อก {discount or '0'}% แบบนี้ ของมีจำนวนจำกัด รีบกดก่อนของหมดนะ!",
        f"ล้างคลังลดราคาไปถึง {discount or '0'}% ช้ากว่านี้ระวังของหมดเกลี้ยง อดช้อนนะครับ!",
        f"เจ้ามือดัมพ์ล้างสต็อกจัดให้เลยส่วนลด {discount or '0'}% ตุนได้รีบตุนด่ันๆ เลย!",
        f"โอกาสทองดีลล้างพอร์ต ลดหนัก {discount or '0'}% สั่งซื้อด่วนก่อนสต็อกจะเป็นศูนย์ครับ"
    ]

    # Define variations lists for MICRO-TRIGGER
    mt_headers = [
        "⚡ **RADAR SIGNAL: MICRO-TRIGGER - ดีลล่าแต้ม ราคาหลักหน่วย/สิบประจำวัน !**",
        "⚡ **PRICE RADAR: MICRO-TRIGGER - ดีลลับราคาประหยัดหลักหน่วยสิบด่วน !**",
        "⚡ **RADAR SIGNAL: MICRO-TRIGGER - ดีลล่าแต้มราคาจิ๋วพิเศษประจำวัน !**",
        "⚡ **PRICE RADAR: MICRO-TRIGGER - ซิกแนลดีลราคาหลักหน่วยสิบราคาประหยัดที่สุด !**",
        "⚡ **RADAR SIGNAL: MICRO-TRIGGER - จุดซื้อดีลเล็กแต้มใหญ่ ประจำวัน !**"
    ]
    mt_intros = [
        "ระบบเรดาร์หลังบ้านตรวจพบดีลราคาพิเศษที่ถูกลดราคาลงจนเหลือแค่หลักหน่วยหรือหลักสิบ! คัดมาเฉพาะร้านแท้ชัวร์ (Official Mall) ที่คนซื้อจริงรีวิวให้คะแนนสูงลิ่ว เพื่อความคุ้มค่าคุ้มราคาขั้นสุด!",
        "เรดาร์หลังบ้านตรวจพบดีลราคาจิ๋วหลักสิบที่ลดกระหน่ำเพื่อเรียกลูกค้าเข้าร้าน! คัดเฉพาะร้านแท้มีอย./การันตี รีวิวงดงาม ปลอดภัยไม่ต้องคิดเยอะช็อปได้เลย!",
        "ตรวจพบดีลซิกแนลราคาถูกระดับไม่เกรงใจใคร เหลือแค่หลักหน่วยหรือหลักสิบเท่านั้น! ร้านแท้ทางการรีวิวแน่น ดีลล่าแต้มล่าโปรสุดๆ!",
        "ระบบวิเคราะห์ราคาจับดีลราคาจิ๋วเด็ดๆ ประจำชั่วโมง ราคาหลักหน่วยหรือหลักสิบเท่านั้น คัดมาแต่ร้านทางการยอดรีวิวดี ปลอดภัยไร้กังวลชัวร์!",
        "ซิกแนลล่าแต้มตรวจเจอดีลลับราคาประหยัดหลักหน่วยสิบที่ถูกใจสายประหยัด! คัดเฉพาะร้านแท้ Official ที่คะแนนรีวิวทะลุเป้า ปลอดภัยไม่ดอยแน่นอน!"
    ]
    mt_connectors = [
        "นี่คือโอกาสทองในการเก็บดีลล่าแต้มที่ปลอดภัยและประหยัดเงินที่สุดในตลาดตอนนี้:",
        "จุดเข้าซื้อดีลราคาจิ๋วที่ประหยัดเงินในกระเป๋าที่สุดเวลานี้:",
        "ดีลประหยัดงบที่คุ้มค่าและไร้ความเสี่ยงที่สุดสำหรับวันนี้:",
        "จ่ายเบาๆ เก็บแต้มเน้นๆ ความเสี่ยงต่ำสุดในตลาดตอนนี้:",
        "ดีลประหยัดแบบไม่ต้องคิดเยอะ คุ้มค่าที่สุดประจำชั่วโมง:"
    ]
    mt_fallbacks = [
        f"ดีลพิเศษราคาประหยัดแบบนี้ ลดโหดถึง {discount or '0'}% รีบกดไปล่าแต้มด่วนก่อนหมดเวลานะครับ",
        f"ประหยัดเงินสุดๆ ดีลลดถึง {discount or '0'}% ราคาขยี้ตาแบบนี้ต้องรีบสอยไปใช้แล้ว!",
        f"ราคาจิ๋วแต่ความคุ้มแจ๋ว ลดถึง {discount or '0'}% สั่งซื้อติดบ้านไว้ด่วนๆ เลยครับ!",
        f"จ่ายเพียงนิดเดียวได้ส่วนลดถึง {discount or '0'}% คุ้มกว่านี้ไม่มีอีกแล้ว สอยด่วนเลย!",
        f"ดีลเล็กพริกขี้หนูลดไปถึง {discount or '0'}% รีบสั่งไปเก็บแต้ม/ใช้งานกันนะครับ",
        f"ราคาเบาหวิวเหมือนได้ฟรี ลดแรงถึง {discount or '0'}% กดด่วนก่อนดีลลับจะปิดตัวครับ"
    ]

    caption_clean = None
    prompt = None

    # Run Ollama for dynamic analysis sentence if one of the 3 templates
    if source_filename in ('GRADE AAA', 'VOLUME SHOCK', 'MICRO-TRIGGER'):
        prompt = f"""คุณคือเซียนหุ้นข้างบ้านที่ชอบวิเคราะห์ราคาสินค้าของใช้ทั่วไปแบบปั่นๆ ฮาๆ
ช่วยเขียนประโยคแนะนำ/วิเคราะห์สินค้าสั้นๆ แค่ 1 ประโยค (ย้ำ: ความยาวห้ามเกิน 1 ประโยคเด็ดขาด และห้ามยาวเกิน 25 คำ) โดยให้เข้ากับสินค้า '{title}' ที่ลดราคาถึง {discount}%
ใช้คำศัพท์แนวเทรดหุ้นปั่นๆ ผสมภาษาชาวบ้าน เช่น "กราฟหลุดแนวรับแล้ว ราคานี้ต้องช้อน", "ราคาดิ่งเหวแบบนี้รีบสอยด่วน", "โวลุ่มซื้อขายไหลเข้าหนาแน่นแบบนี้ต้องจัด" เป็นต้น
พยายามคิดคำพูดใหม่ๆ ให้มีความหลากหลายและสร้างสรรค์ในทุกๆ ครั้ง อย่าใช้แต่ประโยคเดิมซ้ำๆ
ห้ามเกริ่นนำ ห้ามทวนชื่อสินค้าหรือเขียนราคาตัวเลข ซ้ำซ้อน ห้ามใส่แฮชแท็ก ห้ามมีเครื่องหมายคำพูด ตอบสั้นๆ แค่ประโยคนั้นตรงๆ เลย"""
        
        try:
            ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
            model = get_ollama_model()
            url = f"{ollama_url}/api/generate"
            headers = {"Content-Type": "application/json"}
            body = {
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 1.2,
                    "num_predict": 50
                }
            }
            req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers)
            # Long timeout of 60 seconds as requested (user doesn't mind waiting to get unique content)
            with urllib.request.urlopen(req, timeout=60) as res:
                res_body = json.loads(res.read().decode('utf-8'))
                ollama_res = res_body.get('response', '').strip()
                if ollama_res:
                    caption_clean = ollama_res.strip().strip('"').strip("'").strip('()').strip('（）').strip()
        except Exception:
            pass

        # Compile final output based on selected template
        if source_filename == 'GRADE AAA':
            header = random.choice(aaa_headers)
            intro = random.choice(aaa_intros)
            connector = random.choice(aaa_connectors)
            if not caption_clean:
                caption_clean = random.choice(aaa_fallbacks)
            final_caption = f"""{header}
🛒 พิกัดร้านแท้ตรงจากเรดาร์: {link}
───────────────────

📊 {intro}

{connector}

🛡 Target Lock 01: {title}
📉 Data: เจ้ามือทุบราคา {discount}% ลดโหดเหลือแค่ {sale_price} บาท (จากยอดดอย {price} บาท)
⭐ Social Proof: รีวิวแน่นปึ้ก {rating} ดาว ยอดขายพุ่งทะลุ {sold} ชิ้นแล้ว ปลอดภัยไม่ซื้อของแพงแน่นอน!

{caption_clean}

#ช้อนได้ช้อน #สแกนราคาจริงพิทักษ์กระเป๋าเงิน #ของดีราคาดิ่ง"""
            return prompt, final_caption, None

        elif source_filename == 'VOLUME SHOCK':
            header = random.choice(vs_headers)
            intro = random.choice(vs_intros)
            connector = random.choice(vs_connectors)
            if not caption_clean:
                caption_clean = random.choice(vs_fallbacks)
            final_caption = f"""{header}
🛒 พิกัดร้านแท้ตรงจากเรดาร์: {link}
───────────────────

📊 {intro}

{connector}

🛡 Target Lock 01: {title}
📉 Data: เจ้ามือทุบราคา {discount}% ลดโหดเหลือแค่ {sale_price} บาท (จากยอดดอย {price} บาท)
⭐ Social Proof: รีวิวแน่นปึ้ก {rating} ดาว ยอดขายพุ่งทะลุ {sold} ชิ้นแล้ว ปลอดภัยไม่ซื้อของแพงแน่นอน!

{caption_clean}

#เคลียร์สต็อกด่วน #สแกนราคาจริงพิทักษ์กระเป๋าเงิน #ของดีราคาดิ่ง"""
            return prompt, final_caption, None

        elif source_filename == 'MICRO-TRIGGER':
            header = random.choice(mt_headers)
            intro = random.choice(mt_intros)
            connector = random.choice(mt_connectors)
            if not caption_clean:
                caption_clean = random.choice(mt_fallbacks)
            final_caption = f"""{header}
🛒 พิกัดร้านแท้ตรงจากเรดาร์: {link}
───────────────────

📊 {intro}

{connector}

🛡 Target Lock 01: {title}
📉 Data: เจ้ามือทุบราคา {discount}% ลดโหดเหลือแค่ {sale_price} บาท (จากยอดดอย {price} บาท)
⭐ Social Proof: รีวิวแน่นปึ้ก {rating} ดาว ยอดขายพุ่งทะลุ {sold} ชิ้นแล้ว ปลอดภัยไม่ซื้อของแพงแน่นอน!

{caption_clean}

#ดีลล่าแต้ม #สแกนราคาจริงพิทักษ์กระเป๋าเงิน #ของดีราคาดิ่ง"""
            return prompt, final_caption, None

    else:
        # Default copywriter template (other campaigns)
        title_norm = title.replace(" ", "")
        desc_norm = description.replace(" ", "") if description else ""
        is_buy_1_get_1 = False
        for kw in ["1แถม1", "1ฟรี1", "ซื้อ1แถม1", "ซื้อ1ฟรี1", "ซื้อหนึ่งแถมหนึ่ง", "ซื้อหนึ่งฟรีหนึ่ง"]:
            if kw in title_norm or kw in desc_norm:
                is_buy_1_get_1 = True
                break
        
        prompt = f"""คุณคือผู้เชี่ยวชาญด้านการเขียนคำโฆษณา (Copywriter) สำหรับขายสินค้าบน Facebook และโซเชียลมีเดีย
ช่วยเขียนแคปชั่นโปรโมทสินค้า Shopee ชวนเชื่อ ชวนซื้อ น่าดึงดูดใจ และเน้นความคุค่า

ข้อมูลสินค้า:
- ชื่อสินค้า: {title}
- รายละเอียดสินค้า: {description[:300] if description else 'ไม่มีรายละเอียด'}...
- ราคาปกติ: {price or 'ไม่มีข้อมูล'} บาท
- ราคาลดพิเศษ: {sale_price or 'ไม่มีข้อมูล'} บาท
- ส่วนลด: {discount or 'ไม่มีข้อมูล'}%
- ลิงก์สั่งซื้อสินค้า (Affiliate Link): {link}
- คะแนนรีวิวสินค้า: {rating or 'ไม่มีข้อมูล'}
- จำนวนที่ขายได้แล้ว: {sold or 'ไม่มีข้อมูล'}
"""
        if is_buy_1_get_1:
            prompt += "\n**เงื่อนไขพิเศษ: สินค้านี้มีโปรโมชันพิเศษแบบ \"1 แถม 1\" หรือ \"1 ฟรี 1\"**\nกรุณาเน้นโปรโมชัน 1 แถม 1 อย่างเด่นชัดในแคปชั่น เพื่อกระตุ้นความน่าสนใจสูงสุด!"
        else:
            prompt += "\nกรุณาเขียนเน้นราคาลดพิเศษและส่วนลดเพื่อกระตุ้นความสนใจสูงสุด"
            
        prompt += """
แนวทางการเขียน:
1. ใช้ภาษาไทยที่สนุกสนาน เป็นกันเอง น่าตื่นเต้น และน่าเชื่อถือ
2. ใช้ Emoji เพื่อเพิ่มความน่าสนใจและแบ่งหัวข้อให้อ่านง่าย
3. โครงสร้างแคปชั่น:
   - พาดหัวเด็ดๆ (Hook) ที่ดึงดูดคนอ่านทันที
   - รายละเอียดความคุ้มค่า/จุดเด่นของสินค้า
   - Call to Action (ชวนจิ้มสั่งซื้อที่ลิงก์สั่งซื้อสินค้า)
   - แทรกแฮชแท็กที่เกี่ยวข้อง (เช่น #Shopee #โปรดีบอกต่อ #1แถม1 เป็นต้น)
4. ห้ามแปลงลิงก์สั่งซื้อสินค้าเป็นรูปแบบ Markdown link (เช่น [ข้อความ](url)) โดยเด็ดขาด! ให้เขียนเป็นลิงก์ดิบ (Raw URL) ตรงๆ เท่านั้น (เช่น https://shope.ee/...) เพื่อให้สามารถนำไปโพสต์ลง Facebook แล้วระบบของ Facebook โหลดพรีวิวรูปภาพและข้อมูลลิงก์ขึ้นมาแสดงได้ถูกต้อง
5. ในเนื้อหาแคปชั่น ห้ามเขียนลิงก์รูปภาพสินค้า (cf.shopee.co.th) ลงไปเด็ดขาด ให้ใช้เฉพาะลิงก์สั่งซื้อสินค้าเท่านั้น
6. ผลลัพธ์ต้องส่งคืนเฉพาะข้อความแคปชั่นภาษาไทยเท่านั้น ไม่ต้องเกริ่นนำหรือแสดงรายละเอียดการคิดวิเคราะห์ใดๆ ทั้งสิ้น
"""

    # Use Local Ollama exclusively as requested by the user
    try:
        ollama_url = os.getenv("OLLAMA_API_URL", "http://localhost:11434")
        model = get_ollama_model()
        url = f"{ollama_url}/api/generate"
        headers = {"Content-Type": "application/json"}
        body = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }
        req = urllib.request.Request(url, data=json.dumps(body).encode('utf-8'), headers=headers)
        # 180 second timeout for local inference in case of high load
        with urllib.request.urlopen(req, timeout=180) as res:
            res_body = json.loads(res.read().decode('utf-8'))
            caption = res_body.get('response', '').strip()
            if caption:
                if source_filename == 'GRADE AAA':
                    # Clean the AI text response to only include the humor block nicely
                    caption_clean = caption.strip().strip('"').strip("'").strip('()').strip('（）').strip()
                    final_caption = f"""🟢 **RADAR SIGNAL: GRADE AAA - สัญญาณซื้อด่วน !**

📊 รายงานด่วนจาก Price Radar:
ระบบเรดาร์หลังบ้านตรวจพบสินค้า 'ของมันต้องมี' ที่ผ่านเกณฑ์ความปลอดภัยขั้นสุด! คัดมาเฉพาะร้านแท้ชัวร์ (Official Mall) ที่คนซื้อจริงรีวิวให้ทะลุ 4.8 ดาว แถมตอนนี้ราคาถูกทุบดิ่งลงมาต่ำกว่าเส้นค่าเฉลี่ยซะจนต้องขยี้ตา!

นี่ไม่ใช่แค่ของถูก แต่คือ 'จุดเข้าซื้อที่ปลอดภัยที่สุด' ในตลาดตอนนี้:

🛡 Target Lock 01: {title}
📉 Data: เจ้ามือทุบราคา {discount}% ลดโหดเหลือแค่ {sale_price} บาท (จากยอดดอย {price} บาท)
⭐ Social Proof: รีวิวแน่นปึ้ก {rating} ดาว ยอดขายพุ่งทะลุ {sold} ชิ้นแล้ว ปลอดภัยไม่ซื้อของแพงแน่นอน!
🛒 พิกัดร้านแท้ตรงจากเรดาร์: {link}

{caption_clean}

#ช้อนได้ช้อน #สแกนราคาจริงพิทักษ์กระเป๋าเงิน #ของดีราคาดิ่ง"""
                    return prompt, final_caption, None
                else:
                    return prompt, caption, None
            else:
                return prompt, None, "Local Ollama returned an empty response"
    except Exception as e:
        return prompt, None, f"Local Ollama failed: {e}"

def log_prompt_history(db_path, itemid, prompt, response, error_message):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO ai_prompt_history (itemid, prompt, response, error_message) VALUES (?, ?, ?, ?)",
            (itemid, prompt, response, error_message)
        )
        conn.commit()
    except Exception as e:
        print(f"Failed to log prompt history: {e}")
    finally:
        conn.close()
