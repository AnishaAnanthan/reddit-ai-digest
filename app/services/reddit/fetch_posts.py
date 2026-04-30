import asyncio
import logging
import time
from typing import Dict

from app.config.settings import settings
from app.models.post_models import RawPost
from app.services.reddit.fetch_comments import fetch_comments_for_post
from app.services.reddit.reddit_client import reddit_get

logger = logging.getLogger(__name__)

async def _process_post(item: dict, subreddit: str) -> RawPost:
    post_data = item.get("data", {})
    post_id = post_data.get("id", "")
    permalink = post_data.get("permalink", "")
    created_utc = post_data.get("created_utc", 0.0)

    comments = await fetch_comments_for_post(post_id, subreddit)

    return RawPost(
        post_id=post_id,
        title=post_data.get("title", ""),
        content=post_data.get("selftext", ""),
        score=post_data.get("score", 0),
        url=f"https://www.reddit.com{permalink}",
        subreddit=subreddit,
        created_utc=created_utc,
        comments=comments,
    )

async def fetch_category_posts(subreddit: str, category: str) -> list[dict]:
    """
    Fetches posts for a specific category (hot, new, top, etc.)
    """
    params = {"limit": settings.POST_LIMIT}
    if category == "top":
        params["t"] = "day"
        
    path = f"/r/{subreddit}/{category}.json"
    try:
        data = await reddit_get(path, params=params)
        return data.get("data", {}).get("children", [])
    except Exception as e:
        logger.error(f"Failed to fetch {category} posts for r/{subreddit}: {e}")
        return []

async def fetch_subreddit_posts(subreddit: str) -> list[RawPost]:
    """
    Fetches posts from multiple categories for a single subreddit,
    deduplicates them, and filters for posts from the last 24 hours.
    """
    categories = ["hot", "new", "top", "rising", "best"]
    
    # Fetch all categories concurrently
    category_tasks = [fetch_category_posts(subreddit, cat) for cat in categories]
    category_results = await asyncio.gather(*category_tasks)
    
    # Deduplicate posts using post_id and filter by age
    unique_posts_data: Dict[str, dict] = {}
    now = time.time()
    one_day_ago = now - (24 * 3600)
    
    # For logging purposes, show the window in IST (UTC+5:30)
    from datetime import datetime, timedelta, timezone
    ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    ist_start = ist_now - timedelta(hours=24)
    logger.info(f"r/{subreddit}: Fetching posts from {ist_start.strftime('%H:%M')} yesterday to {ist_now.strftime('%H:%M')} today (IST)")
    
    total_found = 0
    rejected_by_age = 0
    
    for children in category_results:
        total_found += len(children)
        for item in children:
            post_data = item.get("data", {})
            post_id = post_data.get("id")
            created_utc = post_data.get("created_utc", 0)
            
            # Keep if unique and from today (last 24h)
            if post_id and post_id not in unique_posts_data:
                if created_utc >= one_day_ago:
                    unique_posts_data[post_id] = item
                else:
                    rejected_by_age += 1

    if not unique_posts_data:
        logger.warning(f"r/{subreddit}: Found {total_found} posts total, but {rejected_by_age} were too old. 0 fresh posts found.")
        return []

    logger.info(f"r/{subreddit}: {total_found} found across categories -> {len(unique_posts_data)} unique & fresh today. ({rejected_by_age} filtered by age)")

    # Process all unique posts to fetch comments
    tasks = [_process_post(item, subreddit) for item in unique_posts_data.values()]
    return await asyncio.gather(*tasks)

async def fetch_top_posts() -> list[RawPost]:
    """
    Fetches today's posts from all categories across all configured subreddits.
    """
    tasks = [fetch_subreddit_posts(sub) for sub in settings.SUBREDDITS]
    results = await asyncio.gather(*tasks)
    
    all_posts = []
    for subreddit_posts in results:
        all_posts.extend(subreddit_posts)

    return all_posts
