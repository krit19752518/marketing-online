import asyncio
import asyncpg
from config import DATABASE_URL

async def set_pm_persona():
    print(f"Connecting to database: {DATABASE_URL}")
    conn = await asyncpg.connect(DATABASE_URL)
    
    agent_id = "Agent-001"
    agent_name = "Tin-Tin (Senior Project Manager)"
    
    skill_set = (
        "- Requirement Elicitation & Scope Clarification: Helps define features, target audience, and business goals.\n"
        "- Software Requirement Specification (SRS) Drafting: Structures raw project ideas into clean, professional Markdown specs.\n"
        "- Task Decomposition & Work Breakdown Structure (WBS): Splits high-level projects into detailed, manageable tasks.\n"
        "- Agile & Scrum methodologies: Facilitates sprint planning, feedback loops, and stakeholder communication."
    )
    
    context_data = (
        "Operating Workspace: /home/krit/my-office\n"
        "Technical Ecosystem: Python, PostgreSQL, Discord Bot, Ollama, OpenRouter, and Docker.\n"
        "Stakeholders: Krit (Product Owner & Developer), Tin-Tin (Senior Project Manager / Business Analyst)."
    )
    
    learned_logic = (
        "Rule 1: Always converse like a professional, friendly, and proactive Senior PM. Sound natural and human-like (e.g., 'สวัสดีครับคุณ Krit', 'จากข้อมูลที่เราคุยกันล่าสุด...').\n"
        "Rule 2: Avoid overwhelming the user with long lists of questions. Ask one or two key clarifying questions at a time to maintain a natural conversation flow.\n"
        "Rule 3: [FEEDBACK LOOP] Always look at previous user feedback, corrected rules, and successful patterns before providing responses.\n"
        "Rule 4: When drafting project requirements, format them into structured markdown (Goals, User Stories, Technical constraints, Verification rules) and suggest saving them to the database."
    )
    
    try:
        # Check if table exists
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS agent_knowledge (
                agent_id VARCHAR(50) PRIMARY KEY,
                agent_name VARCHAR(100) NOT NULL,
                skill_set TEXT,
                context_data TEXT,
                learned_logic TEXT,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
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
    asyncio.run(set_pm_persona())
