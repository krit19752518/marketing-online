import asyncio
import asyncpg

async def main():
    conn = await asyncpg.connect("postgresql://n8n_user:n8n_secure_pass_2026@localhost:5435/my_office_db")
    rows = await conn.fetch("SELECT agent_id, agent_name, skill_set FROM agent_knowledge")
    for r in rows:
        print(f"ID: {r['agent_id']} | Name: {r['agent_name']}")
    await conn.close()

asyncio.run(main())
