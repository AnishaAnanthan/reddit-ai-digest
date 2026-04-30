import asyncio
from dotenv import load_dotenv
load_dotenv()

from app.services.ai.ai_client import ai_client

async def main():
    print("Testing LLM connection...")
    response = await ai_client.call_ai(
        system_prompt="You are a helpful assistant.",
        user_content="Say 'LLM is working!' and nothing else."
    )
    if response:
        print(f"SUCCESS: {response}")
    else:
        print("FAILED: No response received. Check your API key and model settings.")

asyncio.run(main())
