import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

from app.services.ai.ai_client import ai_client

async def main():
    print("Testing LLM with larger input...")
    input_text = "Repeat 'Hello' 50 times."
    response = await ai_client.call_ai(
        system_prompt="You are a helpful assistant.",
        user_content=input_text
    )
    print(f"Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())
