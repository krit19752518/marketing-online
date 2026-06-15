import asyncio
import asyncpg

# Database Connection URLs
DB_5432 = "postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing"
DB_5435 = "postgresql://n8n_user:n8n_secure_pass_2026@localhost:5435/my_office_db"

personas_keywords = {
    "MD": "อนุมัติ,งบประมาณ,กลยุทธ์,ทิศทางบริษัท,สัญญา,ลงทุน,นโยบาย",
    "PM": "ตามงาน,ส่งงานเมื่อไหร่,มอบหมายงาน,วางแผน,Timeline,Gantt Chart,ปัญหา/Blocker",
    "SA": "ออกแบบฐานข้อมูล,ER Diagram,Flowchart,API Spec,Requirements,โครงสร้างข้อมูล",
    "DevLeader": "Architecture,Code Review,มาตรฐานโค้ด,เลือก Library,วิธีแก้บั๊กยากๆ,Git Structure",
    "Programmer_Backend": "API Development,Database Query,FastAPI,Node.js,C#,.NET,Integration,Server Logic",
    "Programmer_Frontend": "UI/UX Component,Flutter,React,HTML/CSS,Web/App Screen,เชื่อม API หน้าบ้าน,State",
    "Tester": "Test Case,เจอ Bug,ระบบพังตรงไหน,รีพอร์ตบั๊ก,ตรวจสอบความถูกต้อง,ลองกดเทส"
}

async def update_db(db_url):
    print(f"Connecting to {db_url}...")
    try:
        conn = await asyncpg.connect(db_url)
        
        # 1. Alter table to add keywords column if it doesn't exist
        print("Checking/Adding keywords column...")
        await conn.execute("""
            ALTER TABLE agent_knowledge ADD COLUMN IF NOT EXISTS keywords text;
        """)
        
        # 2. Update keywords for each persona
        for agent_id, keywords in personas_keywords.items():
            await conn.execute("""
                UPDATE agent_knowledge
                SET keywords = $2, updated_at = CURRENT_TIMESTAMP
                WHERE agent_id = $1
            """, agent_id, keywords)
            print(f"  Updated keywords for: {agent_id}")
            
        await conn.close()
        print(f"Database {db_url} updated successfully!\n")
    except Exception as e:
        print(f"Error updating database {db_url}: {e}\n")

async def main():
    await update_db(DB_5432)
    await update_db(DB_5435)

if __name__ == "__main__":
    asyncio.run(main())
