import httpx
from openai import AsyncOpenAI
from app.config.settings import settings
import logging
import time

logger = logging.getLogger(__name__)

class AIClient:
    def __init__(self):
        # Set timeout on the client itself (httpx-level) for reliable enforcement
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=httpx.Timeout(60.0, connect=10.0),
        )
        
    async def call_ai(self, system_prompt: str, user_content: str, temperature: float = 0.3) -> str:
        """
        Generic method to call OpenAI API.
        """
        model = settings.OPENAI_MODEL
        logger.info(f"Calling AI with model: {model}")
        logger.info(f"Payload size: system_prompt={len(system_prompt)} chars, user_content={len(user_content)} chars")
        start = time.time()
        try:
            logger.info("Attempting chat completion...")
            response = await self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                temperature=temperature,
            )
            elapsed = round(time.time() - start, 2)
            content = response.choices[0].message.content or ""
            logger.info(f"AI response received in {elapsed}s — {len(content)} chars")
            return content
        except httpx.TimeoutException:
            elapsed = round(time.time() - start, 2)
            logger.error(f"OpenAI API call timed out after {elapsed}s")
            return ""
        except Exception as e:
            elapsed = round(time.time() - start, 2)
            logger.error(f"OpenAI API call failed after {elapsed}s: {type(e).__name__}: {e}")
            return ""

# Singleton instance
ai_client = AIClient()
