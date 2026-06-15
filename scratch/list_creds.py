import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://n8n_user:n8n_secure_password_99@localhost:5432/content_marketing")
    columns = await conn.fetch("SELECT column_name FROM information_schema.columns WHERE table_name = 'agent_knowledge'")
    print("Columns in content_marketing.agent_knowledge:")
    for c in columns:
        print(c["column_name"])
    await conn.close()

asyncio.run(main())
