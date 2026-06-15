import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from ollama_client import OllamaClient

@pytest.mark.asyncio
async def test_get_chat_response_ollama_success():
    client = OllamaClient()
    client.use_openrouter = False  # Force Ollama
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "model": "gemma2:2b",
        "message": {
            "role": "assistant",
            "content": "Hello! I am ready to help you."
        }
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        reply = await client.get_chat_response(
            system_instruction="You are a helper.",
            history=[{"role": "user", "message": "Hi"}],
            user_message="Hello again"
        )
        
        assert reply == "Hello! I am ready to help you."
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "/api/chat" in args[0]

@pytest.mark.asyncio
async def test_get_chat_response_openrouter_success():
    client = OllamaClient()
    client.use_openrouter = True
    client.openrouter_api_key = "test-key"
    
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "This is from OpenRouter!"
                }
            }
        ]
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        
        reply = await client.get_chat_response(
            system_instruction="Instruction",
            history=[],
            user_message="Hello"
        )
        
        assert reply == "This is from OpenRouter!"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "openrouter.ai" in args[0]
        assert kwargs["headers"]["Authorization"] == "Bearer test-key"
