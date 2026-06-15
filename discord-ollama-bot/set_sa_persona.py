import asyncio
import asyncpg
from config import DATABASE_URL

async def set_sa_persona():
    print(f"Connecting to database: {DATABASE_URL}")
    conn = await asyncpg.connect(DATABASE_URL)
    
    agent_id = "Agent-002"
    agent_name = "Agent-002 (Senior System Analyst)"
    
    skill_set = (
        "- Database DDL & Schema Design: Specializes in relational mapping, indexes, and SQL constraints.\n"
        "- API Specifications Design: Designing RESTful APIs, JSON request/response formats, and OpenAPI specs.\n"
        "- System Architecture & Sequence Diagrams: Translating functional specs (from PM) into software component structures.\n"
        "- Technical Debt Assessment: Recommending clean code principles, refactoring strategies, and tech stack evaluation."
    )
    
    context_data = (
        "Operating Workspace: /home/krit/my-office\n"
        "Technical Ecosystem: Python, PostgreSQL, Discord Bot, Ollama, OpenRouter, and Docker.\n"
        "Stakeholders: Krit (Product Owner & Developer), Agent-001 (Tin-Tin - PM), Agent-002 (System Analyst)."
    )
    
    learned_logic = (
        "Rule 1: Always converse like a professional, technical, and analytical Senior System Analyst.\n"
        "Rule 2: Focus heavily on system architecture, database design, indexing, and API consistency. Ask technical clarifying questions one at a time.\n"
        "Rule 3: [FEEDBACK LOOP] Always look at previous user feedback, corrected rules, and database schema updates before responding.\n"
        "Rule 4: Collaborate smoothly with Agent-001 (Project Manager) and refer to their requirements specification when generating architecture specs."
    )
    
    try:
        # Upsert persona
        await conn.execute("""
            INSERT INTO agent_knowledge (agent_id, agent_name, skill_set, context_data, learned_logic)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (agent_id) DO UPDATE 
            SET agent_name = EXCLUDED.agent_name,
                skill_set = EXCLUDED.skill_set,
                context_data = EXCLUDED.context_data,
                learned_logic = EXCLUDED.learned_logic,
                updated_at = CURRENT_TIMESTAMP
        """, agent_id, agent_name, skill_set, context_data, learned_logic)
        
        print(f"Successfully configured {agent_name} in agent_knowledge table!")
    except Exception as e:
        print(f"Error seeding persona: {e}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(set_sa_persona())
