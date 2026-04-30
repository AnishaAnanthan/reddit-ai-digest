import asyncio
import logging
import json
import sys
import os

# Add the project root to sys.path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.reddit.fetch_posts import fetch_subreddit_posts
from app.services.ai.stage2_subreddit_ranker import rank_subreddit_posts
from app.utils.output_formatter import format_top_posts_text
from app.config.settings import settings

# Setup simple logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

async def verify_step_by_step():
    # Force UTF-8 for printing to avoid Windows encoding issues
    def safe_print(text):
        try:
            sys.stdout.buffer.write(text.encode('utf-8'))
            sys.stdout.buffer.write(b'\n')
        except:
            print(text.encode('ascii', 'ignore').decode('ascii'))

    safe_print("\n" + "="*50)
    safe_print("REDDIT AI AGENT V2 - STEP-BY-STEP VERIFICATION")
    safe_print("="*50 + "\n")

    target_subreddit = settings.SUBREDDITS[0]

    # --- STEP 1: FETCHING (Multi-Category + 24h Filter) ---
    safe_print(f"[STEP 1]: Fetching posts from r/{target_subreddit}...")
    safe_print("(Scanning hot, new, top, rising, best feeds...)")
    
    raw_posts = await fetch_subreddit_posts(target_subreddit)
    
    safe_print(f"SUCCESS: Found {len(raw_posts)} unique posts from the last 24 hours.")
    if raw_posts:
        sample = raw_posts[0]
        safe_print(f"   Sample Post: '{sample.title}'")
        safe_print(f"   Created At: {sample.created_utc} (Timestamp)")
        safe_print(f"   Score: {sample.score} | Comments: {len(sample.comments)}")
    else:
        safe_print("ERROR: No posts found. Ensure your Reddit connection is active.")
        return

    safe_print("\n" + "-"*30 + "\n")

    # --- STEP 2: RANKING (AI Composite Logic) ---
    safe_print(f"[STEP 2]: Applying AI Composite Ranking for r/{target_subreddit}...")
    safe_print("(Evaluating Popularity + Comment Quality + Reasoning...)")
    
    ranked_posts = await rank_subreddit_posts(target_subreddit, raw_posts)
    
    if ranked_posts:
        safe_print(f"SUCCESS: AI successfully ranked {len(ranked_posts)} posts.")
        # Show the first ranked post as an example of the new schema
        top = ranked_posts[0]
        safe_print("\n--- Top Ranked Post Example ---")
        safe_print(f"Title: {top.title}")
        safe_print(f"Importance Score: {top.importance_score}/10")
        safe_print(f"AI Reasoning: {top.reasoning}")
    else:
        safe_print("ERROR: Ranking failed. Check your AI_API_KEY.")
        return

    safe_print("\n" + "-"*30 + "\n")

    # --- STEP 3: FORMATTING (Email Body) ---
    safe_print("[STEP 3]: Formatting the final Email Digest...")
    
    email_body = format_top_posts_text(ranked_posts)
    
    safe_print("SUCCESS: Final Output Generated:")
    safe_print("\n" + "="*50)
    safe_print(email_body)
    safe_print("="*50)

if __name__ == "__main__":
    asyncio.run(verify_step_by_step())
