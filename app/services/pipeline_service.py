import asyncio
import logging
from app.services.reddit.fetch_posts import fetch_top_posts
from app.services.ai.stage2_subreddit_ranker import rank_subreddit_posts
from app.services.notifications.email_sender import send_results_email
from app.utils.output_formatter import format_top_posts_text
from app.config.settings import settings

logger = logging.getLogger(__name__)

async def run_full_ranking_pipeline():
    """
    v2: Fetches all categories, filters for last 24h, and ranks by importance.
    No rejection filter is used.
    """
    logger.info("Starting v2 full ranking pipeline...")
    
    # 1) Fetch raw posts (already handles all categories + 24h filter + deduplication)
    raw_posts = await fetch_top_posts()
    if not raw_posts:
        logger.warning("No fresh posts found on Reddit today.")
        return {"status": "error", "message": "No fresh posts found on Reddit today."}

    # 2) Group posts by subreddit for ranking
    posts_by_subreddit: dict[str, list] = {}
    for post in raw_posts:
        posts_by_subreddit.setdefault(post.subreddit, []).append(post)

    # 3) Per-subreddit ranking
    subreddit_rankings: dict[str, list] = {}
    merged_ranked_posts = []
    
    for subreddit in settings.SUBREDDITS:
        subreddit_posts = posts_by_subreddit.get(subreddit, [])
        if not subreddit_posts:
            logger.info(f"No posts to rank for r/{subreddit}")
            continue
            
        ranked = await rank_subreddit_posts(subreddit, subreddit_posts)
        subreddit_rankings[subreddit] = [post.model_dump() for post in ranked]
        merged_ranked_posts.extend(ranked)

    if not merged_ranked_posts:
        logger.warning("No posts ranked successfully.")
        return {
            "status": "error",
            "message": "No posts ranked successfully.",
            "raw_count": len(raw_posts),
        }

    # 4) Format and Email
    # Note: Using the top 10 globally ranked posts for the email
    # Or just all merged posts if the user prefers. 
    # For now, we'll keep the top selections across all subreddits.
    final_output_text = format_top_posts_text(merged_ranked_posts)
    logger.info(f"Final ranked posts formatted. Length: {len(final_output_text)}")

    email_status = "sent"
    email_error = None
    try:
        await asyncio.to_thread(send_results_email, final_output_text)
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        email_status = "failed"
        email_error = str(e)

    return {
        "status": "success",
        "raw_count": len(raw_posts),
        "subreddit_rankings": subreddit_rankings,
        "merged_count": len(merged_ranked_posts),
        "final_output_text": final_output_text,
        "email_status": email_status,
        "email_error": email_error,
    }
