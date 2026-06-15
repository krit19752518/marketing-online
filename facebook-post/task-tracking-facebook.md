# Task Tracking: Shopee Affiliate AI Caption Dashboard

## เป้าหมายหลัก

สร้างระบบ backend + dashboard สำหรับบริหาร Shopee affiliate product feed ให้:
- แต่ละ row เป็นการ์ดงาน
- มองเห็นสถานะ workflow ชัดเจน
- ส่งข้อมูลให้ AI สร้างข้อความเชิญชวน
- ให้ผู้ใช้งานรีวิวและอนุมัติเองก่อนโพส

---

## Task List

### ✅ Phase 1: Core MVP

- [x] task-001 สร้างฐานข้อมูล `shopee_affiliate_cards`
- [x] task-002 ออกแบบ schema และสร้าง table
- [x] task-003 สร้าง index สำหรับ `status`, `discount_percentage`, `updated_at`
- [x] task-004 สร้าง import pipeline จาก CSV ลง DB
- [x] task-005 ทำ backend API พื้นฐานสำหรับ `GET /cards` และ `GET /cards/{itemid}`
- [x] task-006 ทำ backend API สำหรับ `POST /cards/import`
- [x] task-007 สร้าง dashboard หน้า list แสดงการ์ดสินค้า
- [x] task-008 สร้างฟิลด์ status workflow และสถานะเริ่มต้น `new`
- [x] task-009 สร้าง endpoint `POST /cards/{itemid}/generate` สำหรับสั่ง AI
- [x] task-010 สร้าง UI ให้แก้ไข `ai_caption` และบันทึก `reviewer_note`

### ✅ Phase 2: Workflow + AI

- [ ] task-011 ออกแบบ prompt template สำหรับกลุ่ม “1 แถม 1”
- [ ] task-012 ทำ logic status transition: `new` → `ai_generated` → `review` → `approved`
- [ ] task-013 สร้าง queue / worker สำหรับ generate caption อัตโนมัติ
- [ ] task-014 บันทึก prompt history และ AI response
- [ ] task-015 เพิ่มปุ่ม `Regenerate caption` ใน UI
- [ ] task-016 เพิ่มฟิลด์ `status = posted` และ `status = rejected`

### ✅ Phase 3: Dashboard & Monitoring

- [ ] task-017 สร้าง Kanban board ตามสถานะ
- [ ] task-018 เพิ่ม filter: `Official Shop`, `Lowest Price Guarantee`, `Discount >= 30%`
- [ ] task-019 สร้าง summary widget: จำนวน `new`, `ai_generated`, `review`, `approved`, `posted`
- [ ] task-020 สร้าง activity log / history view
- [ ] task-021 สร้างฟีเจอร์ search / sort / pagination

### ✅ Phase 4: Quality & Testing

- [ ] task-022 เขียน unit test สำหรับ schema / migration
- [ ] task-023 เขียน unit test สำหรับ import CSV
- [ ] task-024 เขียน unit test สำหรับ backend API
- [ ] task-025 เขียน unit test สำหรับ AI prompt generation logic
- [ ] task-026 เขียน frontend test สำหรับ action buttons
- [ ] task-027 เขียน end-to-end test: import → generate → review → approve

### ✅ Phase 5: Deployment และ configuration

- [ ] task-028 ตั้งค่า environment variables
- [ ] task-029 เขียน script `run backend`, `run frontend`, `setup database`
- [ ] task-030 วางแผน deploy / local development

---

## Detailed Tasks

### task-001 - task-003: Database design

- [x] task-001 สร้าง table `shopee_affiliate_cards`
- [x] task-002 สร้างคอลัมน์หลักและ metadata
- [x] task-003 สร้าง index `status`, `discount_percentage`, `updated_at`

**Columns**:
- `itemid`, `title`, `price`, `sale_price`, `discount_percentage`
- `stock`, `item_sold`, `item_rating`, `likes_count`
- `is_official_shop`, `is_preferred_shop`, `has_lowest_price_guarantee`
- `product_link`, `product_short_link`, `image_link`, `description`
- `status`, `ai_prompt`, `ai_caption`, `reviewer_note`, `assigned_to`
- `source_filename`, `feed_date`, `created_at`, `updated_at`

### task-004: Import / ETL

- [x] task-004 สร้าง import script/endpoint
- [x] task-004a map CSV columns ตาม schema
- [x] task-004b sanitize text, ลบ null bytes
- [x] task-004c upsert เมื่อ `itemid` ซ้ำ
- [x] task-004d set default `status = 'new'`

### task-005 - task-010: Backend API

- [x] task-005 `GET /cards` ดึงรายการ + filter + pagination
- [x] task-006 `GET /cards/{itemid}` ดึง detail
- [x] task-007 `POST /cards/import` import CSV
- [x] task-008 `PATCH /cards/{itemid}` update status, note, caption
- [x] task-009 `POST /cards/{itemid}/generate` สั่ง AI สร้าง caption
- [ ] task-010 `POST /cards/batch-generate` generate หลายรายการ

### task-011 - task-016: AI caption generation

- [ ] task-011 สร้าง prompt template แบบไทยสำหรับ "1 แถม 1"
- [ ] task-012 เขียน service/worker สร้าง caption จาก prompt
- [ ] task-013 เก็บ `ai_prompt` และ `ai_caption`
- [ ] task-014 บันทึก prompt history และ error logs
- [ ] task-015 ทำปุ่ม `Regenerate caption`
- [ ] task-016 ทำระบบเปลี่ยน status และ lock review

### task-017 - task-021: Dashboard

- [ ] task-017 สร้าง list view แบบการ์ด
- [ ] task-018 สร้าง Kanban board (status column)
- [ ] task-019 สร้าง filters / search / sort
- [ ] task-020 เพิ่ม heads-up summary counts
- [ ] task-021 เพิ่ม activity log / last updated

### task-022 - task-027: Tests

- [ ] task-022 migration/schema tests
- [ ] task-023 import/ETL tests
- [ ] task-024 backend API tests
- [ ] task-025 AI prompt and generation logic tests
- [ ] task-026 frontend interaction tests
- [ ] task-027 full workflow E2E tests

### task-028 - task-030: Deployment

- [ ] task-028 set environment variables (
  - `DATABASE_URL`
  - `AI_API_KEY`
  - `AI_ENDPOINT`
  - `RUN_MODE`
  )
- [ ] task-029 create run scripts
- [ ] task-030 document setup and run instructions

---

## Notes

- เฟสแรกให้โฟกัสที่ `new → ai_generated → review → approved`
- ยังไม่ต้องเชื่อมโพสอัตโนมัติ
- ให้ dashboard แยกชัดว่า card ไหนยังไม่ถูกสร้าง caption
- เก็บ `product_short_link` เป็นช่องสำคัญสำหรับโพสเร็ว
- ใช้ prompt context ว่าเป็น "1 แถม 1" / "1 ฟรี 1"
