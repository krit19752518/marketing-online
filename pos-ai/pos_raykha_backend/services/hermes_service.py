import re

class HermesService:
    # Dictionary of inappropriate words and their polite replacements
    BANNED_WORDS = {
        "กู": "เรา",
        "มึง": "เธอ",
        "เหี้ย": "แย่",
        "สัส": "เพื่อน",
        "ควย": "...",
    }

    @classmethod
    def filter_inbound_prompt(cls, user_message: str) -> str:
        """
        Sanitizes user messages by replacing inappropriate words.
        """
        if not user_message:
            return ""
        cleaned = user_message
        for rude_word, replacement in cls.BANNED_WORDS.items():
            cleaned = re.sub(rude_word, replacement, cleaned, flags=re.IGNORECASE)
        return cleaned

    @classmethod
    def enrich_system_prompt(cls, db_schema_description: str = "") -> str:
        """
        Returns the system instruction prompt to customize LLM behavior,
        injecting the DB Schema instructions so it can output SQL queries.
        """
        base_prompt = (
            "คุณคือเลขาส่วนตัว AI ชื่อ 'RayKha' (เรขา) สุภาพ อ่อนน้อม วัยทำงาน "
            "พูดคุยตอบกลับอย่างเป็นมืออาชีพ มีหางเสียงลงท้ายด้วย 'ค่ะ' หรือ 'นะคะ' เสมอ "
            "ห้ามแทนตัวว่า 'ฉัน' หรือ 'ผม' ให้แทนตัวเองว่า 'ดิฉัน' หรือ 'เลขา' และเรียกผู้ใช้ว่า 'บอส' หรือ 'ท่าน' เสมอ "
            "หลีกเลี่ยงการลากตัวสะกดเสียงยาวเกินสองตัว (เช่น ห้ามตอบว่า 'ค่ะะะ', 'ค่าาา') เพื่อให้อ่านออกเสียงแบบ Text-to-Speech ได้ถูกต้อง "
            "\n"
            "ความสามารถพิเศษของคุณคือการช่วยบอสวิเคราะห์ข้อมูลและดึงรายงานยอดขาย สต๊อกสินค้า หรือโต๊ะจากฐานข้อมูลของร้าน "
            "เมื่อบอสถามคำถามเกี่ยวกับยอดขาย กำไร สต๊อกสินค้า หรือข้อมูลทางธุรกิจ ให้ปฏิบัติดังนี้:\n"
            "1. คุณต้องเขียนคำสั่ง SQL Query (PostgreSQL SELECT เท่านั้น) ที่ถูกต้องเพื่อดึงคำตอบจากตารางที่กำหนด\n"
            "2. เขียนคำสั่ง SQL ให้อยู่ในบล็อกโค้ด ```sql ... ``` เสมอ\n"
            "3. อย่าอธิบายตัว SQL ยาวเกินไป เน้นการตอบผลลัพธ์ข้อมูลเมื่อระบบนำผลลัพธ์กลับมาส่งให้คุณ\n"
            "4. ห้ามเขียนคำสั่งแก้ไข/ลบ/เพิ่มข้อมูล (INSERT, UPDATE, DELETE, DROP) เป็นอันขาด ให้ใช้ SELECT ในการดึงข้อมูลอ่านอย่างเดียว (Read-only) เท่านั้น\n"
        )
        
        if db_schema_description:
            base_prompt += f"\nนี่คือ Schema ฐานข้อมูลของร้านบอสที่คุณใช้สอบถามได้:\n{db_schema_description}\n"
            
        return base_prompt

    @classmethod
    def filter_outbound_response(cls, ai_response: str) -> str:
        """
        Cleans AI response before sending it to the client.
        Reduces repeating Thai trailing characters (e.g. 'มากกกก' -> 'มาก').
        """
        if not ai_response:
            return ""
            
        cleaned = ai_response
        # Find 3 or more repetitions of any Thai character and reduce them to one
        # Thai character range: \u0e01-\u0e5b
        cleaned = re.sub(r'([\u0e01-\u0e5b])\1{2,}', r'\1', cleaned)
        
        return cleaned
