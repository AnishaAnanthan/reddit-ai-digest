import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.services.ai.ai_client import ai_client

async def test_ai_filtering():
    print("--- AI Filtering Test: AI Updates Theme ---")
    
    # 1. Prepare Mock Data (AI Updates Posts)
    mock_posts = [
        {
            "post_id": "ai_001",
            "title": "GPT-5 potentially launching this summer, leak suggests 20% improvement in reasoning",
            "content": "A reliable source within OpenAI suggests that GPT-5 is currently in training and could be released by June. Initial benchmarks show a significant jump in multi-step reasoning and logical consistency compared to GPT-4 Turbo.",
            "score": 4500
        },
        {
            "post_id": "ai_002",
            "title": "How to use Gemini 1.5 Pro's 2M context window for code analysis",
            "content": "Gemini 1.5 Pro now supports 2 million tokens. This guide shows how to upload an entire legacy codebase to find security vulnerabilities and refactoring opportunities using Python scripts.",
            "score": 2800
        },
        {
            "post_id": "ai_003",
            "title": "AI is going to take all our jobs!!! I am scared",
            "content": "I just saw a video of a robot making coffee. It's over for us. What are we going to do? Is anyone else worried about the future of employment?",
            "score": 120
        },
        {
            "post_id": "ai_004",
            "title": "Nvidia's Blackwell architecture: A deep dive into B200 specs and performance",
            "content": "The B200 GPU features 20 petaflops of FP4 power and a new NVLink interconnect. This post breaks down the architectural changes from Hopper and what it means for LLM training costs.",
            "score": 3200
        },
        {
            "post_id": "ai_005",
            "title": "Check out my new AI cat photo generator! (link to spam)",
            "content": "I made a site that generates cats wearing hats. Please visit my site and subscribe to my newsletter for more cat pics. Link: bit.ly/spam-cats",
            "score": 15
        },
        {
            "post_id": "ai_006",
            "title": "OpenAI's Search Engine rumors: Will it finally kill Google Search?",
            "content": "Speculation is growing that OpenAI will launch a search product next week. While rumors have circulated before, the recent domain registration 'search.chatgpt.com' adds fuel to the fire.",
            "score": 1800
        },
        {
            "post_id": "ai_007",
            "title": "Apple's M4 chip benchmarks show massive AI performance gains for local LLMs",
            "content": "Early benchmarks of the M4 iPad Pro show the Neural Engine is 2x faster than M2. This allows for running 7B parameter models entirely on-device with 30 tokens/sec speed.",
            "score": 2100
        }
    ]

    # 2. Define the Custom Prompt
    system_prompt = """
    You are an AI research analyst. Your task is to filter a list of Reddit posts to find the most significant "AI Updates".
    
    Criteria for "Top 3" posts:
    1. Technical Depth: Posts that explain architecture or technical breakthroughs.
    2. Significant News: Major announcements from leading labs (OpenAI, Google, Anthropic, Nvidia).
    3. Practical Utility: Guides or tools that provide immediate value to developers or researchers.
    
    Filter out:
    - Fear-mongering (AI taking jobs without data).
    - Spam/Self-promotion (AI art generators, newsletters).
    - Low-effort speculation without evidence.
    
    Output Format (JSON):
    [
      {
        "post_id": "string",
        "title": "string",
        "rank": number (1-3),
        "reason": "short explanation of why this is in the top 3"
      }
    ]
    Return ONLY the JSON array.
    """

    user_content = json.dumps(mock_posts, indent=2)

    print(f"\nSending {len(mock_posts)} mock posts to AI for filtering...")
    
    # 3. Call AI
    ai_output = await ai_client.call_ai(system_prompt, user_content)
    
    # 4. Display Results
    if ai_output:
        try:
            # Clean output if it has markdown blocks
            clean_output = ai_output.strip()
            if clean_output.startswith("```json"):
                clean_output = clean_output[7:-3].strip()
            elif clean_output.startswith("```"):
                clean_output = clean_output[3:-3].strip()
                
            results = json.loads(clean_output)
            print("\n--- TOP 3 AI UPDATES ---")
            for item in results:
                print(f"\nRank {item.get('rank')}: {item.get('title')}")
                print(f"ID: {item.get('post_id')}")
                print(f"Reason: {item.get('reason')}")
        except Exception as e:
            print(f"\nError parsing AI response: {e}")
            print(f"Raw Output: {ai_output}")
    else:
        print("\nFAILED: No response from AI.")

if __name__ == "__main__":
    asyncio.run(test_ai_filtering())
