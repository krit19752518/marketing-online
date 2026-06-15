import logging
import httpx
from typing import List, Dict
from config import (
    OLLAMA_BASE_URL, 
    OLLAMA_MODEL, 
    OPENROUTER_API_KEY, 
    OPENROUTER_MODEL, 
    USE_OPENROUTER
)

logger = logging.getLogger(__name__)

class OllamaClient:
    def __init__(self):
        self.ollama_url = OLLAMA_BASE_URL.rstrip("/") + "/api/chat"
        self.ollama_model = OLLAMA_MODEL
        
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.openrouter_api_key = OPENROUTER_API_KEY
        self.openrouter_model = OPENROUTER_MODEL
        self.use_openrouter = USE_OPENROUTER

    async def get_chat_response(
        self, 
        system_instruction: str, 
        history: List[Dict[str, str]], 
        user_message: str,
        model: str = None
    ) -> str:
        """
        Sends system instruction, history, and user message to either local Ollama or OpenRouter.
        """
        # Build standard messages array
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
            
        for msg in history:
            messages.append({"role": msg["role"], "content": msg["message"]})
            
        messages.append({"role": "user", "content": user_message})

        if self.use_openrouter and self.openrouter_api_key:
            return await self._call_openrouter(messages, model)
        else:
            return await self._call_ollama(messages, model)

    async def _call_openrouter(self, messages: List[Dict], model: str = None) -> str:
        target_model = model or self.openrouter_model
        payload = {
            "model": target_model,
            "messages": messages
        }
        headers = {
            "Authorization": f"Bearer {self.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "GritTin Discord Bot"
        }
        
        logger.info(f"Sending request to OpenRouter: {self.openrouter_url} with model {target_model}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                response = await client.post(self.openrouter_url, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                if "choices" in data and len(data["choices"]) > 0:
                    choice = data["choices"][0]
                    if "message" in choice and "content" in choice["message"]:
                        return choice["message"]["content"]
                
                logger.error(f"Unexpected OpenRouter API response format: {data}")
                return "Error: Unexpected response format from OpenRouter."
            except httpx.HTTPError as e:
                logger.error(f"HTTP error connecting to OpenRouter: {e}")
                return f"Error connecting to OpenRouter server: {e}"
            except Exception as e:
                logger.error(f"Unexpected error in OpenRouter client call: {e}")
                return f"An unexpected error occurred: {e}"

    async def _call_ollama(self, messages: List[Dict], model: str = None) -> str:
        target_model = model or self.ollama_model
        payload = {
            "model": target_model,
            "messages": messages,
            "stream": False
        }
        
        logger.info(f"Sending request to Ollama: {self.ollama_url} with model {target_model}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(self.ollama_url, json=payload)
                response.raise_for_status()
                data = response.json()
                
                if "message" in data and "content" in data["message"]:
                    return data["message"]["content"]
                
                logger.error(f"Unexpected Ollama API response format: {data}")
                return "Error: Unexpected response format from Ollama."
            except httpx.HTTPError as e:
                logger.error(f"HTTP error connecting to Ollama: {e}")
                return f"Error connecting to local Ollama server: {e}"
            except Exception as e:
                logger.error(f"Unexpected error in Ollama client call: {e}")
                return f"An unexpected error occurred: {e}"
