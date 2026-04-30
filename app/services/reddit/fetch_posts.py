import asyncio
import logging

from app.config.settings import settings
from app.models.post_models import RawPost
from app.services.reddit.fetch_comments import fetch_comments_for_post
from app.services.reddit.reddit_client import reddit_get

logger = logging.getLogger(__name__)

async def _process_post(item: dict, subreddit: str) -> RawPost:
    post_data = item.get("data", {})
    post_id = post_data.get("id", "")
    permalink = post_data.get("permalink", "")

    comments = await fetch_comments_for_post(post_id, subreddit)

    return RawPost(
        post_id=post_id,
        title=post_data.get("title", ""),
        content=post_data.get("selftext", ""),
        score=post_data.get("score", 0),
        url=f"https://www.reddit.com{permalink}",
        subreddit=subreddit,
        comments=comments,
    )

async def fetch_subreddit_posts(subreddit: str) -> list[RawPost]:
    """
    Fetches top posts for a single subreddit.
    """
    data = await reddit_get(
        f"/r/{subreddit}/top.json",
        params={"limit": settings.POST_LIMIT, "t": "day"}
    )

    children = data.get("data", {}).get("children", [])
    if not children:
        logger.warning(f"No posts returned for r/{subreddit} (may be private or blocked).")
        return []

    logger.info(f"Fetched {len(children)} posts from r/{subreddit}.")

    tasks = [_process_post(item, subreddit) for item in children]
    return await asyncio.gather(*tasks)

async def fetch_top_posts() -> list[RawPost]:
    """
    Fetches top posts from all configured subreddits concurrently.
    """
    tasks = [fetch_subreddit_posts(sub) for sub in settings.SUBREDDITS]
    results = await asyncio.gather(*tasks)
    
    all_posts = []
    for subreddit_posts in results:
        all_posts.extend(subreddit_posts)

    return all_posts
