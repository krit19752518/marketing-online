import logging
import asyncpg
from typing import List, Dict, Optional
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Global pool reference
_pool: Optional[asyncpg.Pool] = None

async def init_db_pool() -> asyncpg.Pool:
    """Initializes the asyncpg connection pool."""
    global _pool
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=10)
            logger.info("Database connection pool initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise e
    return _pool

async def close_db_pool():
    """Closes the database connection pool."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
        logger.info("Database connection pool closed.")

def get_pool() -> asyncpg.Pool:
    """Returns the current active connection pool."""
    if _pool is None:
        raise RuntimeError("Database connection pool is not initialized. Call init_db_pool first.")
    return _pool

async def get_agent_knowledge(agent_id: str = 'Agent-001') -> Optional[Dict]:
    """
    Fetches the agent persona context and instructions from database.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT agent_id, agent_name, skill_set, context_data, learned_logic 
            FROM agent_knowledge 
            WHERE agent_id = $1
            """,
            agent_id
        )
        if row:
            return dict(row)
        return None

async def get_chat_history(session_id: str, limit: int = 15) -> List[Dict]:
    """
    Retrieves the recent chat history for a given channel / session_id.
    Returns list of dicts with 'role' and 'message'.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT role, message 
            FROM chat_history 
            WHERE session_id = $1 
            ORDER BY id DESC 
            LIMIT $2
            """,
            session_id, limit
        )
        # Reverse to get chronological order (oldest first for model context)
        history = [{"role": r["role"], "message": r["message"]} for r in reversed(rows)]
        return history

async def add_chat_message(session_id: str, role: str, message: str) -> None:
    """
    Inserts a new message to the chat history table.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO chat_history (session_id, role, message) 
            VALUES ($1, $2, $3)
            """,
            session_id, role, message
        )

async def upsert_project_spec(session_id: str, raw_input: str, formatted_spec: str) -> None:
    """
    Saves or updates requirement specifications for a session.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO project_specs (session_id, raw_input, formatted_spec, status)
            VALUES ($1, $2, $3, 'draft')
            ON CONFLICT (session_id) 
            DO UPDATE SET 
                raw_input = EXCLUDED.raw_input,
                formatted_spec = EXCLUDED.formatted_spec,
                updated_at = CURRENT_TIMESTAMP
            """,
            session_id, raw_input, formatted_spec
        )

async def save_memory(session_id: str, context_category: str, key_summary: str) -> None:
    """
    Saves or updates memory summaries for a session/channel.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO memory_store (session_id, context_category, key_summary)
            VALUES ($1, $2, $3)
            ON CONFLICT (session_id, context_category) 
            DO UPDATE SET 
                key_summary = EXCLUDED.key_summary,
                updated_at = CURRENT_TIMESTAMP
            """,
            session_id, context_category.strip(), key_summary.strip()
        )

async def load_memories(session_id: str) -> List[Dict]:
    """
    Loads all memory summaries for a session.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT context_category, key_summary, updated_at 
            FROM memory_store 
            WHERE session_id = $1 
            ORDER BY context_category
            """,
            session_id
        )
        return [dict(r) for r in rows]

