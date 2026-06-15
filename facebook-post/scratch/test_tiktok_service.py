import sys
import os

# Adjust path to import tiktok_service
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from tiktok_service import generate_slide_2_value_text, clean_state, get_product_anatomy_en, generate_tiktok_caption, generate_tiktok_3_slides_text, clean_currency_text
import json

class TestTikTokService(unittest.TestCase):
    def test_clean_state(self):
        # Test basic sanitization
        input_str = "Watermelon cream Jula's Herb sachet pouch pink red sensor light"
        output_str = clean_state(input_str)
        # Forbidden: watermelon, jula's herb, sachet, pouch, pink, red
        # They should be removed case-insensitively
        print(f"Sanitized: '{output_str}'")
        self.assertNotIn("watermelon", output_str.lower())
        self.assertNotIn("jula's herb", output_str.lower())
        self.assertNotIn("sachet", output_str.lower())
        self.assertNotIn("pouch", output_str.lower())
        self.assertNotIn("pink", output_str.lower())
        self.assertNotIn("red", output_str.lower())
        self.assertIn("sensor light", output_str)

    def test_generate_slide_2_value_text(self):
        # Test cleaning decimal strings and float values
        price_info = {
            "price": "790.0",
            "sale_price": 629.0,
            "discount_percentage": "20.0%"
        }
        text = generate_slide_2_value_text(price_info)
        print("Generated Slide 2 copy:")
        print(text)
        # Check no decimals exist in formatted numbers
        self.assertNotIn(".0", text)
        
        # Check that if we replace 20% and 100% (from ของแท้ 100%), there are no other % symbols
        cleaned_pct = text.replace("20%", "").replace("100%", "")
        self.assertNotIn("%", cleaned_pct)
        
        # Verify it uses either 790 or 629 or 161 (saving_amount = 790 - 629 = 161)
        self.assertTrue(any(x in text for x in ["790", "629", "161"]))

    def test_get_product_anatomy_en_hardware(self):
        title = "Motion Sensor Night Light White circular puck light"
        category = "Electronics"
        anatomy = get_product_anatomy_en(title, category)
        print(f"Anatomy output: {anatomy}")
        self.assertEqual(
            anatomy, 
            "A sleek, minimal white circular motion-sensor puck light, showing its smooth frosted plastic diffuser front and modern round chassis design."
        )

    def test_get_product_anatomy_en_scrunchies(self):
        title = "ยางรัดผมโดนัทผ้าซาตินหลากสี"
        category = "แฟชั่น"
        anatomy = get_product_anatomy_en(title, category)
        print(f"Scrunchies Anatomy output: {anatomy}")
        self.assertEqual(
            anatomy,
            "A pack of colorful elastic fabric hair scrunchies and cute hair ties"
        )

    def test_get_product_anatomy_en_fallback(self):
        title = "Dr. Jill Plant-Based Protein"
        category = "สุขภาพ"
        anatomy = get_product_anatomy_en(title, category)
        print(f"Fallback Anatomy output: {anatomy}")
        self.assertEqual(
            anatomy,
            "A retail package of Dr. Jill Plant-Based Protein"
        )

    def test_get_product_anatomy_en_innerdeo(self):
        title = "[ช้อปครบ รับฟรี] Dr.PONG InnerDeo Japanese Persimmon Powder อาหารเสริมลดกลิ่นกาย กลิ่นแก่ กลิ่นปาก"
        category = "หมวดหมู่อื่นๆ"
        anatomy = get_product_anatomy_en(title, category)
        print(f"InnerDeo Anatomy output: {anatomy}")
        self.assertEqual(
            anatomy,
            "A white plastic supplement medicine pill bottle jar with a white screw cap lid"
        )

    def test_get_product_anatomy_en_vaseline_glutahya(self):
        title = "วาสลีน กลูต้า-ไฮยา ดิวอี้ เรเดียนซ์ โลชั่น 330 มล. หลอด"
        category = "ความงาม"
        anatomy = get_product_anatomy_en(title, category)
        print(f"Vaseline Gluta-Hya Anatomy output: {anatomy}")
        self.assertEqual(
            anatomy,
            "A premium flat plastic squeeze tube packaged lotion, standing vertically upside down upon its white cap, featuring the authentic Vaseline Gluta-Hya branding colors."
        )

    def test_generate_tiktok_caption_hardware(self):
        # Mock card
        card = {
            "title": "Motion Sensor Night Light",
            "description": "Smart LED lamp with sensor auto turn on/off",
            "price": "499.0",
            "sale_price": "299.0",
            "discount_percentage": "40.0",
            "category": "Electronics"
        }
        
        import urllib.request
        from unittest.mock import patch, MagicMock
        
        mock_response = MagicMock()
        # Python context manager mock enter return
        mock_response.__enter__.return_value = mock_response
        # Mock Ollama output json format
        mock_response.read.return_value = json.dumps({
            "response": json.dumps({
                "slide_1_hook": "เปิดไฟอัตโนมัติเมื่อเดินผ่าน!",
                "slide_2_value": "โปรโมชั่นจำกัดเวลา!",
                "slide_3_cta": "สั่งซื้อด่วน!",
                "vibe_style_1": "clean studio night light ambient, no watermelon pouch please"
            })
        }).encode('utf-8')
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            res_json_str, error = generate_tiktok_caption(card)
            self.assertIsNone(error)
            data = json.loads(res_json_str)
            print("Generated JSON Response:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # Check Slide 2 prompt has the custom string concatenation
            prompt_bg_2 = data["prompt_bg_2"]
            self.assertIn("A sleek, minimal white circular motion-sensor puck light", prompt_bg_2)
            self.assertIn("Maintain its exact white circular puck shape, electronic plastic casing", prompt_bg_2)
            
            # Check sanitization has removed watermelon/pouch terms
            self.assertNotIn("watermelon", prompt_bg_2.lower())
            self.assertNotIn("pouch", prompt_bg_2.lower())
            self.assertNotIn("watermelon", data["prompt_bg_1"].lower())

    def test_generate_tiktok_caption_scrunchies(self):
        # Mock card with accessories that should NOT be classified as apparel
        card = {
            "title": "ยางรัดผมโดนัทผ้าซาตินหลากสี",
            "description": "ยางมัดผมแฟชั่นสำหรับผู้หญิง",
            "price": "199.0",
            "sale_price": "99.0",
            "discount_percentage": "50.0",
            "category": "แฟชั่น"
        }
        
        import urllib.request
        from unittest.mock import patch, MagicMock
        
        mock_response = MagicMock()
        mock_response.__enter__.return_value = mock_response
        mock_response.read.return_value = json.dumps({
            "response": json.dumps({
                "slide_1_hook": "ยางรัดผมโดนัทสุดน่ารัก!",
                "slide_2_value": "คุ้มสุดๆ!",
                "slide_3_cta": "พิกัดในลิงก์!",
                "vibe_style_1": "cute pastel background"
            })
        }).encode('utf-8')
        
        with patch('urllib.request.urlopen', return_value=mock_response):
            res_json_str, error = generate_tiktok_caption(card)
            self.assertIsNone(error)
            data = json.loads(res_json_str)
            
            # Should NOT use the clothing suspended template (since accessories are excluded)
            # Instead, it should use the geometric podium template!
            prompt_bg_1 = data["prompt_bg_1"]
            self.assertIn("white geometric podium", prompt_bg_1.lower())
            self.assertIn("A pack of colorful elastic fabric hair scrunchies and cute hair ties", prompt_bg_1)
            self.assertNotIn("clothing apparel", prompt_bg_1.lower())

    def test_generate_tiktok_3_slides_text(self):
        # 1. Test Volume Shock
        card_vs = {
            "source_filename": "VOLUME SHOCK",
            "price": 1000,
            "sale_price": 250,
            "discount_percentage": 75
        }
        res_vs = generate_tiktok_3_slides_text(card_vs)
        self.assertEqual(res_vs["slide_1_hook"], "หั่นราคาช็อกโลก 75%!\nปล่อยหลุดมาได้ยังไง?!")
        self.assertEqual(res_vs["slide_2_value"], "จากปกติ 1,000.- ตอนนี้เหลือแค่ 250.- เท่านั้น!")
        self.assertEqual(res_vs["slide_3_cta"], "ระบบจับตาดูอยู่ ราคานี้อยู่ไม่เกิน 2 ชม.\nพิกัดลิงก์หน้าโปรไฟล์!")

        # 2. Test Micro-Trigger
        card_mt = {
            "source_filename": "MICRO-TRIGGER",
            "price": 50,
            "sale_price": 9,
            "discount_percentage": 82
        }
        res_mt = generate_tiktok_3_slides_text(card_mt)
        self.assertEqual(res_mt["slide_1_hook"], "พิกัดของแท้ 9 บาท! มีอยู่จริง ไม่จกตา")
        self.assertEqual(res_mt["slide_2_value"], "แบงค์สิบมีทอน! เหมาตุนไว้ใช้ได้ทั้งปี")
        self.assertEqual(res_mt["slide_3_cta"], "กดตุนด่วนก่อนของขาดตลาด\nจิ้มลิงก์หน้าโปรไฟล์เลย!")

        card_mt_large = {
            "source_filename": "MICRO-TRIGGER",
            "price": 200,
            "sale_price": 49,
            "discount_percentage": 75
        }
        res_mt_large = generate_tiktok_3_slides_text(card_mt_large)
        self.assertEqual(res_mt_large["slide_1_hook"], "พิกัดของแท้ 49 บาท! มีอยู่จริง ไม่จกตา")
        self.assertEqual(res_mt_large["slide_2_value"], "แบงค์ห้าสิบมีทอน! เหมาตุนไว้ใช้ได้ทั้งปี")

        # 3. Test Grade AAA
        card_aaa = {
            "source_filename": "GRADE AAA",
            "price": 1000,
            "sale_price": 500,
            "discount_percentage": 50,
            "item_sold": 25000,
            "likes_count": 5000
        }
        res_aaa = generate_tiktok_3_slides_text(card_aaa)
        self.assertEqual(res_aaa["slide_1_hook"], "ตัวดังมหาชน ยอดขายทะลุ2 หมื่น!\nรอบนี้ลดราคาลงลึกสุด")
        self.assertEqual(res_aaa["slide_2_value"], "ของแท้ 100% จากแบรนด์ตรง\nการันตีโดยผู้ใช้จริงกว่า 25,000 คน")
        self.assertEqual(res_aaa["slide_3_cta"], "คุ้มกว่านี้ไม่มีอีกแล้ว\nเช็คราคาพิเศษที่ลิงก์หน้าโปรไฟล์")

    def test_clean_currency_text(self):
        self.assertEqual(clean_currency_text("฿299.-"), "299.-")
        self.assertEqual(clean_currency_text("฿518"), "518.-")
        self.assertEqual(clean_currency_text("ปกติ ฿399"), "ปกติ 399.-")
        self.assertEqual(clean_currency_text("ลดเหลือ ฿1,200.-"), "ลดเหลือ 1,200.-")

    def test_parse_line_segments(self):
        from tiktok_service import parse_line_segments
        # Segment a line containing ghost price and promo price
        line = "จากปกติ 1,199.- ตอนนี้เหลือแค่ 299.- เท่านั้น!"
        segments = parse_line_segments(line, "1,199.-", "299.-")
        expected = [
            ("จากปกติ ", "primary"),
            ("1,199.-", "ghost"),
            (" ตอนนี้เหลือแค่ ", "primary"),
            ("299.-", "promo"),
            (" เท่านั้น!", "primary")
        ]
        self.assertEqual(segments, expected)
        
        # Segment a line with no special pricing
        line2 = "ระบบจับตาดูอยู่ ราคานี้อยู่ไม่เกิน 2 ชม."
        segments2 = parse_line_segments(line2, None, None)
        self.assertEqual(segments2, [(line2, "primary")])

    def test_compose_tiktok_slide_image(self):
        from tiktok_service import compose_tiktok_slide_image
        from PIL import Image
        import tempfile
        
        # Create a temp output path
        temp_dir = tempfile.mkdtemp()
        out_path = os.path.join(temp_dir, "test_output.png")
        
        # Test drawing slide 2 (exercises segments, strikethrough, and overlay calculations)
        text_content = "จากปกติ 1,199.- ตอนนี้เหลือแค่ 299.- เท่านั้น!"
        price_info = {
            "price": 1199,
            "sale_price": 299,
            "discount_percentage": 75
        }
        
        # Call with bg_image_path=None to trigger fallback background generation
        compose_tiktok_slide_image(
            bg_image_path=None,
            product_image_url=None,
            text_content=text_content,
            output_path=out_path,
            slide_num=2,
            price_info=price_info
        )
        
        # Verify the file was created and is not empty
        self.assertTrue(os.path.exists(out_path))
        self.assertTrue(os.path.getsize(out_path) > 0)
        
        # Verify the file is indeed an image that can be opened
        with Image.open(out_path) as img:
            self.assertEqual(img.size, (1080, 1920))

if __name__ == '__main__':
    unittest.main()
