import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.services.ai.ai_client import ai_client

async def test_comment_analysis():
    print("--- AI Comment Analysis: Incomplete vs Complete Discussions ---")
    
    # 1. Prepare Mock Data (One Post with multiple comments/debates)
    mock_post_with_comments = {
        "post_id": "gpt5_leak_001",
        "title": "GPT-5 potentially launching this summer, leak suggests 20% improvement in reasoning",
        "content": "Speculation is peaking as sources claim GPT-5 training is entering the final stage. The focus is on 'System 2' thinking and logical consistency.",
        "comments": [
            "Finally! I hope they fixed the memory issues. Does anyone know if it will have the same 128k context window?",
            "It's just hype. Every summer they say this. I'll believe it when I see the benchmarks.",
            "I'm curious how this affects current API pricing. If GPT-5 is 20% better, will GPT-4 Turbo become cheaper or be deprecated?",
            "The leak comes from a deleted tweet, so take it with a grain of salt. Here is the link to the archive: [link]",
            "If it really improves reasoning, can it finally solve the 'Stray cat' logic puzzle? Someone should test that immediately.",
            "Meh, local LLMs are catching up anyway. Llama 3 is all I need.",
            "Has anyone heard about the energy requirements for this? Training a 20% better model must be insanely expensive."
        ]
    }

    # 2. Define the Custom Prompt
    system_prompt = """
    You are a discussion moderator. Your goal is to identify "Incomplete Discussions" within Reddit comments.
    
    Definitions:
    - Complete Discussion: The user has stated their opinion, provided a fact, or reached a conclusion. No immediate follow-up or answer is required.
    - Incomplete Discussion: The user has raised an open question, suggested a test, identified a gap in information, or invited further debate. These are "hooks" where a conversation should continue.
    
    Task:
    Analyze the provided comments for the post. Identify the Top 3 "Incomplete" comments that represent the best opportunities for further discussion or research.
    
    Output Format (JSON):
    [
      {
        "comment_text": "string",
        "status": "Incomplete",
        "reason": "Why is this an incomplete discussion?",
        "suggested_followup": "What question should be asked or what research is needed next?"
      }
    ]
    Return ONLY the JSON array.
    """

    user_content = json.dumps(mock_post_with_comments, indent=2)

    print(f"\nAnalyzing {len(mock_post_with_comments['comments'])} comments for post: '{mock_post_with_comments['title']}'")
    
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
            print("\n--- TOP 3 INCOMPLETE DISCUSSIONS (NEEDS FOLLOW-UP) ---")
            for idx, item in enumerate(results):
                print(f"\n[{idx + 1}] Comment: \"{item.get('comment_text')}\"")
                print(f"Reason: {item.get('reason')}")
                print(f"Next Step: {item.get('suggested_followup')}")
        except Exception as e:
            print(f"\nError parsing AI response: {e}")
            print(f"Raw Output: {ai_output}")
    else:
        print("\nFAILED: No response from AI.")

if __name__ == "__main__":
    asyncio.run(test_comment_analysis())
