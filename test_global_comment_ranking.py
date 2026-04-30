import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.services.ai.ai_client import ai_client

async def test_global_comment_ranking():
    print("--- Global AI Discussion Ranking Test ---")
    
    # 1. Prepare 8 Mock Posts with Discussions
    mock_data = [
        {
            "post_id": "p1",
            "title": "GPT-5 potentially launching this summer",
            "comments": [
                "I hope it's better at math.",
                "Does anyone know if the 128k context window is staying or increasing?",
                "Hype again. OpenAI is slow."
            ]
        },
        {
            "post_id": "p2",
            "title": "Nvidia Blackwell B200 Specs Revealed",
            "comments": [
                "208 billion transistors is insane.",
                "What is the expected MSRP for cloud providers per hour?",
                "My 4090 feels old now."
            ]
        },
        {
            "post_id": "p3",
            "title": "Gemini 1.5 Pro: 2M Token Context Window",
            "comments": [
                "I tried it, it's very fast.",
                "Can it actually maintain perfect needle-in-a-haystack retrieval at 2 million tokens?",
                "Google is finally catching up."
            ]
        },
        {
            "p_id": "p4",
            "title": "AI's impact on software engineering jobs",
            "comments": [
                "I'm worried about junior devs.",
                "Are there any peer-reviewed studies comparing productivity with and without Copilot?",
                "AI is just a tool, don't worry."
            ]
        },
        {
            "post_id": "p5",
            "title": "Apple M4 Chip: Built for Local AI",
            "comments": [
                "iPad Pro is too expensive.",
                "What is the maximum parameter size model we can run locally on 16GB of Unified Memory?",
                "Neural Engine looks promising."
            ]
        },
        {
            "post_id": "p6",
            "title": "OpenAI Search Engine rumors heating up",
            "comments": [
                "Google is shaking right now.",
                "How will they handle real-time indexing without a crawler as big as Google's?",
                "I'll stick to Perplexity for now."
            ]
        },
        {
            "post_id": "p7",
            "title": "Devin: The first AI Software Engineer",
            "comments": [
                "It's just a fancy shell script.",
                "Can it handle complex multi-container Docker networking debugging autonomously?",
                "I saw the demo, it's impressive but limited."
            ]
        },
        {
            "post_id": "p8",
            "title": "Llama 3 70B Fine-tuning Guide",
            "comments": [
                "Great tutorial, thanks!",
                "Is QLoRA sufficient for specialized legal domain adaptation, or is full fine-tuning required?",
                "Which GPU should I use for this?"
            ]
        }
    ]

    # 2. Define the Global Ranking Prompt
    system_prompt = """
    You are a high-level AI analyst. You will be provided with multiple Reddit posts and their comments.
    
    Your Task (Two-Step Analysis):
    1. For EACH post, identify exactly ONE "Pending Discussion" (the most important incomplete comment/question).
    2. Compare all those "Pending Discussions" across all posts and select the TOP 3 globally most important ones.
    
    Importance Criteria:
    - High Technical Impact: Questions that clarify performance or architectural limits.
    - Economic/Strategic Significance: Questions about cost, jobs, or market competition.
    - Practical Utility: Questions that, if answered, would help many developers or researchers.
    
    Output Format (JSON):
    {
      "global_top_3": [
        {
          "rank": number (1-3),
          "post_title": "string",
          "pending_comment": "string",
          "reason_for_importance": "string",
          "suggested_next_action": "string",
          "suggested_reply": "A helpful, expert response to the pending comment (max 3 sentences)"
        }
      ]
    }
    Return ONLY the JSON.
    """

    user_content = json.dumps(mock_data, indent=2)

    print(f"\nAnalyzing {len(mock_data)} posts for the most critical pending discussions...")
    
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
            print("\n--- GLOBAL TOP 3 PENDING DISCUSSIONS ---")
            for item in results.get("global_top_3", []):
                print(f"\n[GLOBAL RANK {item.get('rank')}]")
                print(f"Topic: {item.get('post_title')}")
                print(f"Pending Comment: \"{item.get('pending_comment')}\"")
                print(f"Why it matters: {item.get('reason_for_importance')}")
                print(f"Next Action: {item.get('suggested_next_action')}")
                print(f"AI Suggested Reply: \"{item.get('suggested_reply')}\"")
        except Exception as e:
            print(f"\nError parsing AI response: {e}")
            print(f"Raw Output: {ai_output}")
    else:
        print("\nFAILED: No response from AI.")

if __name__ == "__main__":
    asyncio.run(test_global_comment_ranking())
