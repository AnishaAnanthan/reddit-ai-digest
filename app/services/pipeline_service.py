import asyncio
import logging
from app.services.reddit.fetch_posts import fetch_top_posts
from app.services.ai.stage1_filter import filter_posts
from app.services.ai.stage2_subreddit_ranker import rank_subreddit_posts
from app.services.ai.stage3_global_ranker import rank_global_posts
from app.services.notifications.email_sender import send_results_email
from app.utils.output_formatter import format_top_posts_text
from app.config.settings import settings

logger = logging.getLogger(__name__)

async def run_full_ranking_pipeline():
    """
    Encapsulated ranking logic used by both API and Scheduler.
    """
    logger.info("Starting full ranking pipeline...")
    
    # 1) Fetch raw posts
    raw_posts = await fetch_top_posts()
    if not raw_posts:
        logger.warning("No posts fetched from Reddit.")
        return {"status": "error", "message": "No posts fetched from Reddit."}

    # 2) Stage 1 validation/filtering
    stage1_result = await filter_posts(raw_posts, return_diagnostics=True)
    filtered_posts, stage1_diagnostics = stage1_result
    
    stage1_by_subreddit = {subreddit: 0 for subreddit in settings.SUBREDDITS}
    for post in filtered_posts:
        if post.subreddit not in stage1_by_subreddit:
            stage1_by_subreddit[post.subreddit] = 0
        stage1_by_subreddit[post.subreddit] += 1

    if not filtered_posts:
        logger.warning("No posts remained after Stage 1 validation.")
        return {
            "status": "error",
            "message": "No posts remained after Stage 1 validation.",
            "stage1_count": 0,
            "stage1_by_subreddit": stage1_by_subreddit,
            "stage1_diagnostics": stage1_diagnostics,
            "ranking_error_by_subreddit": {
                subreddit: "no_stage1_posts" for subreddit in settings.SUBREDDITS
            },
        }

    # 3) Per-subreddit ranking
    posts_by_subreddit: dict[str, list] = {}
    for post in filtered_posts:
        posts_by_subreddit.setdefault(post.subreddit, []).append(post)

    subreddit_rankings: dict[str, list] = {}
    ranking_error_by_subreddit: dict[str, str | None] = {}
    merged_posts = []
    for subreddit in settings.SUBREDDITS:
        subreddit_posts = posts_by_subreddit.get(subreddit, [])
        ranked = await rank_subreddit_posts(subreddit, subreddit_posts)
        subreddit_rankings[subreddit] = [post.model_dump() for post in ranked]
        merged_posts.extend(ranked)

        if not subreddit_posts:
            ranking_error_by_subreddit[subreddit] = "no_stage1_posts"
        elif not ranked:
            ranking_error_by_subreddit[subreddit] = "ranking_failed_or_empty"
        else:
            ranking_error_by_subreddit[subreddit] = None

    if not merged_posts:
        logger.warning("No posts available after per-subreddit ranking.")
        return {
            "status": "error",
            "message": "No posts available after per-subreddit ranking.",
            "stage1_count": len(filtered_posts),
            "stage1_by_subreddit": stage1_by_subreddit,
            "stage1_diagnostics": stage1_diagnostics,
            "subreddit_rankings": subreddit_rankings,
            "ranking_error_by_subreddit": ranking_error_by_subreddit,
        }

    # 4) Global ranking
    final_top_posts = await rank_global_posts(merged_posts)
    if not final_top_posts:
        logger.error("Global ranking failed.")
        return {
            "status": "error",
            "message": "Global ranking failed.",
            "stage1_count": len(filtered_posts),
            "stage1_by_subreddit": stage1_by_subreddit,
            "stage1_diagnostics": stage1_diagnostics,
            "subreddit_rankings": subreddit_rankings,
            "ranking_error_by_subreddit": ranking_error_by_subreddit,
        }

    # 5) Format and Email
    final_output_text = format_top_posts_text(final_top_posts)
    logger.info(f"Final top posts formatted. Length: {len(final_output_text)}")

    email_status = "sent"
    email_error = None
    try:
        # Use asyncio.to_thread for synchronous email sending
        await asyncio.to_thread(send_results_email, final_output_text)
        logger.info("Email sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        email_status = "failed"
        email_error = str(e)

    return {
        "status": "success",
        "stage1_count": len(filtered_posts),
        "stage1_by_subreddit": stage1_by_subreddit,
        "stage1_diagnostics": stage1_diagnostics,
        "subreddit_rankings": subreddit_rankings,
        "ranking_error_by_subreddit": ranking_error_by_subreddit,
        "merged_count": len(merged_posts),
        "final_count": len(final_top_posts),
        "final_top_posts": [post.model_dump() for post in final_top_posts],
        "final_output_text": final_output_text,
        "email_status": email_status,
        "email_error": email_error,
    }
