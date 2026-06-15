import asyncio
import asyncpg
from config import DATABASE_URL

async def run_migration():
    print(f"Connecting to database to run migration: {DATABASE_URL}")
    conn = await asyncpg.connect(DATABASE_URL)
    try:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS memory_store (
                id SERIAL PRIMARY KEY,
                session_id VARCHAR(100) NOT NULL,
                context_category VARCHAR(50) NOT NULL,
                key_summary TEXT NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_session_category UNIQUE (session_id, context_category)
            );
        """)
        print("Database schema migration completed successfully! Table 'memory_store' created/verified.")
    except Exception as e:
        print(f"Migration error: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
