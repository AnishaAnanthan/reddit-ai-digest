import asyncio
import sys
import os

# Ensure app directory is in path
sys.path.append(os.getcwd())

from app.services.reddit.fetch_posts import fetch_top_posts
from app.services.ai.stage1_filter import filter_posts
from app.services.ai.stage2_subreddit_ranker import rank_subreddit_posts
from app.services.ai.stage3_global_ranker import rank_global_posts
from app.services.notifications.email_sender import send_results_email
from app.utils.output_formatter import format_top_posts_text
from app.config.settings import settings

async def run_pipeline():
    print(">>> Starting full pipeline run...")
    
    # 1. Fetch raw posts
    print(">>> Fetching raw posts from Reddit...")
    raw_posts = await fetch_top_posts()
    if not raw_posts:
        print("!!! No posts fetched from Reddit. Stopping.")
        return

    # 2. Stage 1 filtering
    print(f">>> Filtering {len(raw_posts)} posts (Stage 1)...")
    filtered_posts = await filter_posts(raw_posts)
    print(f">>> Stage 1 kept {len(filtered_posts)} posts.")
    
    if not filtered_posts:
        print("!!! No posts survived Stage 1. Stopping.")
        return

    # 3. Stage 2 per-subreddit ranking
    print(">>> Ranking posts by subreddit (Stage 2)...")
    posts_by_subreddit = {}
    for post in filtered_posts:
        posts_by_subreddit.setdefault(post.subreddit, []).append(post)

    merged_posts = []
    for subreddit in settings.SUBREDDITS:
        subreddit_posts = posts_by_subreddit.get(subreddit, [])
        if not subreddit_posts:
            continue
        ranked = await rank_subreddit_posts(subreddit, subreddit_posts)
        merged_posts.extend(ranked)
    
    print(f">>> Stage 2 produced {len(merged_posts)} ranked posts.")

    if not merged_posts:
        print("!!! No posts available after per-subreddit ranking. Stopping.")
        return

    # 4. Stage 3 global ranking
    print(">>> Global ranking (Stage 3)...")
    final_top_posts = await rank_global_posts(merged_posts)
    
    if not final_top_posts:
        print("!!! Global ranking failed. Stopping.")
        return

    # 5. Format output
    final_output_text = format_top_posts_text(final_top_posts)
    print("\n=== FINAL TOP POSTS ===")
    try:
        print(final_output_text)
    except UnicodeEncodeError:
        print(final_output_text.encode('ascii', 'ignore').decode('ascii'))

    # 6. Send email
    print("\n>>> Sending email...")
    try:
        # Use asyncio.to_thread for blocking email send
        await asyncio.to_thread(send_results_email, final_output_text)
        print(">>> Success! Email sent.")
    except Exception as e:
        print(f"!!! Failed to send email: {e}")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
