import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import asyncio
from app.services.ai.stage1_filter import filter_posts
from app.models.post_models import RawPost

async def main():
    sample = RawPost(
        post_id="test",
        title="Test title",
        content="This is a test post content about finance.",
        score=123,
        url="https://reddit.com/r/test/test",
        subreddit="testsub",
        comments=["Nice post!", "I agree."]
    )
    result, diagnostics = await filter_posts([sample], return_diagnostics=True)
    print("\n=== SINGLE FILTER TEST ===")
    print(f"\nResult count: {len(result)}")
    if result:
        post = result[0]
        print(f"\nPost: {post.title}")
        print(f"  is_valuable_post: {post.is_valuable_post}")
        print(f"  is_valuable_comment: {post.is_valuable_comment}")
        print(f"  discussion_complete: {post.discussion_complete}")
        print(f"  comment_summary: {post.comment_summary}")
        print(f"  reason: {post.reason}")
    
    print(f"\nDiagnostics:")
    print(f"  Total raw posts: {diagnostics.get('total_raw_posts', 0)}")
    print(f"  Posts evaluated: {diagnostics.get('stage1_evaluated_posts', 0)}")
    print(f"  Tier A (post+comments): {diagnostics.get('post_plus_comment_kept', 0)}")
    print(f"  Tier B (post-only): {diagnostics.get('post_only_fallback_kept', 0)}")

if __name__ == "__main__":
    asyncio.run(main())
