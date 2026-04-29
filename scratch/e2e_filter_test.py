"""
End-to-end test: fetch posts from Reddit + run Stage 1 AI filter.
Run from the reddit-ai-agent directory:
    python scratch/e2e_filter_test.py
"""
import sys, os, asyncio, time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force UTF-8 output so Indian Rupee ₹ and other Unicode chars don't crash on Windows
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")

from app.services.reddit.fetch_posts import fetch_top_posts
from app.services.ai.stage1_filter import filter_posts

async def main():
    print("\n" + "="*60)
    print("  END-TO-END FILTER TEST")
    print("="*60)

    # --- Stage 1: Fetch posts from Reddit ---
    print("\n[1/2] Fetching posts from Reddit...")
    t0 = time.time()
    raw_posts = await fetch_top_posts()
    t1 = time.time()
    print(f"      [OK] Fetched {len(raw_posts)} posts in {t1-t0:.1f}s")

    if not raw_posts:
        print("      [X] No posts fetched - check Reddit connectivity.")
        return

    # Show sample of what was fetched
    print(f"\n      Sample posts fetched:")
    for p in raw_posts[:3]:
        print(f"        [{p.subreddit}] {p.title[:70]}...")

    # --- Stage 2: AI Filter ---
    print(f"\n[2/2] Running AI filter on {len(raw_posts)} posts...")
    t2 = time.time()
    filtered, diagnostics = await filter_posts(raw_posts, return_diagnostics=True)
    t3 = time.time()
    print(f"      [OK] AI filter done in {t3-t2:.1f}s - kept {len(filtered)} / {len(raw_posts)} posts")

    # --- Results ---
    print("\n" + "="*60)
    print(f"  RESULTS: {len(filtered)} valuable posts found")
    print(f"  Total time: {t3-t0:.1f}s  (fetch: {t1-t0:.1f}s | AI: {t3-t2:.1f}s)")
    print("="*60)

    print("\n  DIAGNOSTICS:")
    print(f"  Total raw posts: {diagnostics.get('total_raw_posts', 0)}")
    print(f"  Posts evaluated: {diagnostics.get('stage1_evaluated_posts', 0)}")
    print(f"  Tier A (post+comments): {diagnostics.get('post_plus_comment_kept', 0)}")
    print(f"  Tier B (post-only): {diagnostics.get('post_only_fallback_kept', 0)}")
    print(f"  Dropped (comment noise): {diagnostics.get('dropped_due_to_comment_noise', 0)}")
    print(f"  Discussion complete: {diagnostics.get('discussion_complete_count', 0)}")
    print(f"  Discussion incomplete: {diagnostics.get('discussion_incomplete_count', 0)}")

    for i, post in enumerate(filtered, 1):
        print(f"\n  [{i}] [{post.subreddit}] {post.title[:70]}")
        print(f"       category={post.category}  score={post.score}")
        print(f"       is_valuable_post={post.is_valuable_post}  is_valuable_comment={post.is_valuable_comment}")
        print(f"       discussion_complete={post.discussion_complete}")
        print(f"       reason: {post.reason[:100]}")
        print(f"       url: {post.url}")

    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
