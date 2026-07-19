import json
import re
import httpx
from typing import List, Dict, Any, Tuple
from sqlalchemy import text
from sqlalchemy.orm import Session
from config import Config
from services.hermes_service import HermesService

DB_SCHEMA_DESCRIPTION = """
ตารางในฐานข้อมูล (PostgreSQL):

1. ตาราง "Category" (หมวดหมู่สินค้า):
   - id: VARCHAR (Primary Key)
   - name: VARCHAR (ชื่อหมวดหมู่ เช่น "Coffee", "Tea", "Bakery")

2. ตาราง "Product" (สินค้า/เมนู):
   - id: VARCHAR (Primary Key)
   - name: VARCHAR (ชื่อสินค้า เช่น "Cappuccino", "Greentea Latte")
   - price: DOUBLE PRECISION (ราคาสินค้า)
   - categoryId: VARCHAR (Foreign Key อ้างอิง Category.id)

3. ตาราง "ProductOption" (ตัวเลือกเสริม/ท็อปปิ้ง):
   - id: VARCHAR (Primary Key)
   - name: VARCHAR (ชื่อตัวเลือก เช่น "หวาน 50%", "เพิ่มวิปครีม")
   - price: DOUBLE PRECISION (ราคาของตัวเลือกเสริม)
   - productId: VARCHAR (Foreign Key อ้างอิง Product.id)

4. ตาราง "Table" (โต๊ะอาหาร):
   - id: VARCHAR (Primary Key)
   - number: VARCHAR (เลขโต๊ะ เช่น "A1", "B2")
   - status: VARCHAR (สถานะโต๊ะ: "VACANT" (ว่าง), "OCCUPIED" (มีลูกค้า), "BILLING" (เรียกเก็บเงิน))

5. ตาราง "Order" (รายการสั่งซื้อ/ออเดอร์):
   - id: VARCHAR (Primary Key)
   - tableId: VARCHAR (Foreign Key อ้างอิง Table.id, อาจเป็น NULL ได้)
   - status: VARCHAR (สถานะออเดอร์: "PENDING", "PREPARING", "READY", "SERVED", "BILLING", "PAID", "CANCELLED")
   - totalAmount: DOUBLE PRECISION (ราคารวมออเดอร์)
   - createdAt: TIMESTAMP (เวลาที่สั่งซื้อ)

6. ตาราง "OrderItem" (รายการสินค้าในออเดอร์):
   - id: VARCHAR (Primary Key)
   - orderId: VARCHAR (Foreign Key อ้างอิง Order.id)
   - productId: VARCHAR (Foreign Key อ้างอิง Product.id)
   - quantity: INTEGER (จำนวนสินค้าที่สั่ง)
   - subtotal: DOUBLE PRECISION (ราคารวมย่อยของรายการนี้)
   - selectedOpts: JSONB (รายการตัวเลือกเสริมที่เลือก)

7. ตาราง "Transaction" (การชำระเงิน):
   - id: VARCHAR (Primary Key)
   - orderId: VARCHAR (Foreign Key อ้างอิง Order.id)
   - paymentMethod: VARCHAR (ช่องทางชำระเงิน: "CASH", "QR_MOCK", "CREDIT_CARD")
   - amountPaid: DOUBLE PRECISION (จำนวนเงินที่จ่าย)
   - discount: DOUBLE PRECISION (ส่วนลด)
   - change: DOUBLE PRECISION (เงินทอน)
   - createdAt: TIMESTAMP (เวลาที่จ่ายเงิน)

8. ตาราง "Inventory" (คลังสต๊อกวัตถุดิบ):
   - id: VARCHAR (Primary Key)
   - name: VARCHAR (ชื่อวัตถุดิบ เช่น "Fresh Milk", "Coffee Beans")
   - quantity: DOUBLE PRECISION (จำนวนคงเหลือ)
   - unit: VARCHAR (หน่วยนับ เช่น "kg", "litre")
   - minQuantity: DOUBLE PRECISION (จุดสั่งซื้อ/เตือนสต๊อกหมด)
"""

class AIService:
    @staticmethod
    def _is_safe_select_query(query: str) -> bool:
        """
        Ensures the query is read-only.
        Blocks queries containing modification keywords.
        """
        blocked_keywords = ["insert", "update", "delete", "drop", "alter", "truncate", "create", "grant", "revoke"]
        query_lower = query.lower()
        for kw in blocked_keywords:
            # Match word boundary to avoid blocking valid words like 'deletedAt' or 'created'
            if re.search(rf"\b{kw}\b", query_lower):
                return False
        return True

    @classmethod
    async def call_llm(cls, messages: List[Dict[str, str]], temperature: float = 0.1) -> str:
        """
        Sends messages to OpenTyphoon completions endpoint.
        """
        headers = {
            "Authorization": f"Bearer {Config.HERMES_AI_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": Config.HERMES_AI_MODEL,
            "messages": messages,
            "temperature": temperature
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{Config.HERMES_AI_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            result = response.json()
            return result["choices"][0]["message"]["content"]

    @classmethod
    async def ask_raykha(
        cls,
        user_message: str,
        history: List[Dict[str, str]],
        tenant_db: Session
    ) -> Tuple[str, str, str]:
        """
        Processes message with AI:
        1. Sanitize inbound prompt via Hermes.
        2. Generate response/SQL query from LLM.
        3. If SQL is generated: execute it, feed results back to LLM to write final Thai response.
        4. Sanitize outbound response.
        
        Returns Tuple[ai_response, generated_sql, json_query_results]
        """
        # Step 1: Filter inbound message
        cleaned_user_msg = HermesService.filter_inbound_prompt(user_message)
        
        # Build prompt payload
        system_prompt = HermesService.enrich_system_prompt(DB_SCHEMA_DESCRIPTION)
        
        llm_messages = [{"role": "system", "content": system_prompt}]
        for hist_msg in history:
            llm_messages.append({"role": hist_msg["role"], "content": hist_msg["content"]})
        llm_messages.append({"role": "user", "content": cleaned_user_msg})

        # Step 2: Get initial response from LLM
        first_ai_response = await cls.call_llm(llm_messages)
        
        # Check if there is an SQL query block in the response
        sql_match = re.search(r"```sql\s*(.*?)\s*```", first_ai_response, re.DOTALL | re.IGNORECASE)
        
        if sql_match:
            generated_sql = sql_match.group(1).strip()
            
            # Verify SQL is read-only SELECT query
            if not cls._is_safe_select_query(generated_sql):
                error_response = "ดิฉันขอโทษนะคะบอส แต่เพื่อความปลอดภัยของระบบ ดิฉันไม่สามารถรันคำสั่งแก้ไขข้อมูลได้ค่ะ"
                return error_response, generated_sql, json.dumps({"error": "Query rejected. Only SELECT is allowed."})
            
            try:
                # Step 3: Execute query in Tenant DB
                print(f"Agent executing generated SQL: {generated_sql}")
                result_proxy = tenant_db.execute(text(generated_sql))
                
                # Format query results to list of dicts
                rows = result_proxy.fetchall()
                keys = result_proxy.keys()
                query_results = [dict(zip(keys, row)) for row in rows]
                json_results = json.dumps(query_results, default=str, ensure_ascii=False)
                
                # Feed query results back to the LLM to compose a polite response for the boss
                feedback_prompt = (
                    f"นี่คือผลลัพธ์ที่ได้จากการรัน SQL Query ดังกล่าวจากฐานข้อมูลร้านของบอส:\n"
                    f"```json\n{json_results}\n```\n"
                    f"โปรดนำข้อมูลนี้ไปสรุปตอบกลับรายงานเจ้านาย (บอส) ให้เข้าใจง่ายและสุภาพเรียบร้อยที่สุดตามบทบาทเลขา RayKha ค่ะ"
                )
                
                llm_messages.append({"role": "assistant", "content": first_ai_response})
                llm_messages.append({"role": "user", "content": feedback_prompt})
                
                final_ai_response = await cls.call_llm(llm_messages)
                cleaned_final_response = HermesService.filter_outbound_response(final_ai_response)
                
                return cleaned_final_response, generated_sql, json_results
                
            except Exception as e:
                # Handle database errors gracefully and let AI try to explain it or format an error response
                print(f"Error executing query: {e}")
                error_feedback = (
                    f"เกิดข้อผิดพลาดในการรัน SQL Query ในฐานข้อมูลของบอส:\n{str(e)}\n"
                    f"โปรดตอบแจ้งบอสด้วยความสุภาพว่าไม่สามารถดึงข้อมูลได้เนื่องจากมีปัญหาทางเทคนิคดังกล่าวค่ะ"
                )
                llm_messages.append({"role": "assistant", "content": first_ai_response})
                llm_messages.append({"role": "user", "content": error_feedback})
                
                final_ai_response = await cls.call_llm(llm_messages)
                return HermesService.filter_outbound_response(final_ai_response), generated_sql, json.dumps({"error": str(e)})
        else:
            # No SQL query generated, return regular assistant response directly
            return HermesService.filter_outbound_response(first_ai_response), "", ""
