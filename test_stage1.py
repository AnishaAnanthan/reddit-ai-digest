import asyncio
import os
import json
from dotenv import load_dotenv

# Load env before importing app modules
load_dotenv()

from app.services.reddit.fetch_posts import fetch_top_posts
from app.services.ai.stage1_filter import filter_posts

async def main():
    print("--- Testing Stage 1: AI Filter ---")
    
    print("\n1. Fetching raw posts from Reddit...")
    raw_posts = await fetch_top_posts()
    print(f"Fetched {len(raw_posts)} raw posts.")
    
    if not raw_posts:
        print("No posts fetched. Check internet connection or subreddit names.")
        return
        
    print("\n2. Running Stage 1 AI Filter...")
    # This will use the OpenAI API. Make sure OPENAI_API_KEY is in .env
    filtered_posts = await filter_posts(raw_posts)
    
    print(f"\n3. Results (Kept {len(filtered_posts)} posts):")
    for idx, post in enumerate(filtered_posts):
        print(f"\n[Post {idx + 1}]")
        print(f"Title: {post.title}")
        print(f"Reason: {post.reason}")
        print(f"Involvement Needed: {post.involvement_needed}")
        print(f"Actionable Comments: {post.actionable_comments}")
        
    print("\n--- Test Complete ---")

if __name__ == "__main__":
    asyncio.run(main())
