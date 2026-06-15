import pytest
from unittest.mock import AsyncMock, MagicMock, patch, ANY
import db

@pytest.fixture
def mock_pool():
    # Mock pool and connection
    pool = MagicMock()
    conn = AsyncMock()
    
    # Setup connection context manager on pool
    pool.acquire.return_value.__aenter__.return_value = conn
    return pool, conn

@pytest.mark.asyncio
async def test_init_db_pool():
    with patch("asyncpg.create_pool", new_callable=AsyncMock) as mock_create:
        mock_pool = AsyncMock()
        mock_create.return_value = mock_pool
        
        pool = await db.init_db_pool()
        assert pool == mock_pool
        mock_create.assert_called_once()
        
        # Cleanup
        await db.close_db_pool()

@pytest.mark.asyncio
async def test_get_agent_knowledge(mock_pool):
    pool, conn = mock_pool
    # Inject mocked pool
    db._pool = pool
    
    # Mock row returned by fetchrow
    mock_row = {
        "agent_id": "Agent-001",
        "agent_name": "Test Agent",
        "skill_set": "Test Skills",
        "context_data": "Test Context",
        "learned_logic": "Test Logic"
    }
    conn.fetchrow.return_value = mock_row
    
    res = await db.get_agent_knowledge("Agent-001")
    assert res == mock_row
    conn.fetchrow.assert_called_once()

@pytest.mark.asyncio
async def test_get_chat_history(mock_pool):
    pool, conn = mock_pool
    db._pool = pool
    
    mock_rows = [
        {"role": "assistant", "message": "hello!"},
        {"role": "user", "message": "hi"}
    ]
    conn.fetch.return_value = mock_rows
    
    history = await db.get_chat_history("session-123")
    
    # Assert result is reversed (chronological order)
    assert len(history) == 2
    assert history[0] == {"role": "user", "message": "hi"}
    assert history[1] == {"role": "assistant", "message": "hello!"}
    conn.fetch.assert_called_once()

@pytest.mark.asyncio
async def test_add_chat_message(mock_pool):
    pool, conn = mock_pool
    db._pool = pool
    
    await db.add_chat_message("session-123", "user", "hello")
    conn.execute.assert_called_once_with(
        ANY,
        "session-123",
        "user",
        "hello"
    )

@pytest.mark.asyncio
async def test_upsert_project_spec(mock_pool):
    pool, conn = mock_pool
    db._pool = pool
    
    await db.upsert_project_spec("session-123", "raw input", "formatted specs")
    conn.execute.assert_called_once()
    args = conn.execute.call_args[0]
    assert args[1] == "session-123"
    assert args[2] == "raw input"
    assert args[3] == "formatted specs"

@pytest.mark.asyncio
async def test_save_memory(mock_pool):
    pool, conn = mock_pool
    db._pool = pool
    
    await db.save_memory("session-123", "Requirement", "System remembers this requirement")
    conn.execute.assert_called_once()
    args = conn.execute.call_args[0]
    assert args[1] == "session-123"
    assert args[2] == "Requirement"
    assert args[3] == "System remembers this requirement"

@pytest.mark.asyncio
async def test_load_memories(mock_pool):
    pool, conn = mock_pool
    db._pool = pool
    
    mock_rows = [
        {"context_category": "Requirement", "key_summary": "Summary details", "updated_at": "timestamp"}
    ]
    conn.fetch.return_value = mock_rows
    
    memories = await db.load_memories("session-123")
    assert len(memories) == 1
    assert memories[0]["context_category"] == "Requirement"
    assert memories[0]["key_summary"] == "Summary details"
    conn.fetch.assert_called_once()


