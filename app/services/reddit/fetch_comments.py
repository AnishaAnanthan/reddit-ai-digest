import logging
from app.config.settings import settings
from app.models.post_models import CommentRecord
from app.services.reddit.reddit_client import reddit_get
from app.utils.clean_comments import clean_comment_records

logger = logging.getLogger(__name__)

def _extract_comment_nodes(node: dict) -> list[dict]:
    extracted: list[dict] = []

    if not isinstance(node, dict):
        return extracted

    kind = node.get("kind")
    data = node.get("data", {})
    if kind == "t1":
        extracted.append(
            {
                "body": data.get("body", ""),
                "score": data.get("score", 0),
                "author": data.get("author", ""),
                "is_deleted": data.get("body", "") == "[deleted]",
                "is_removed": data.get("body", "") == "[removed]",
                "permalink": data.get("permalink", ""),
            }
        )

    replies = data.get("replies")
    if isinstance(replies, dict):
        for child in replies.get("data", {}).get("children", []):
            extracted.extend(_extract_comment_nodes(child))

    return extracted


async def fetch_comments_for_post(post_id: str, subreddit: str) -> list[CommentRecord]:
    """
    Fetches the top comments for a given Reddit post using the public JSON API.
    """
    data = await reddit_get(
        f"/r/{subreddit}/comments/{post_id}.json",
        params={"limit": settings.COMMENT_LIMIT, "depth": 2, "sort": "top"}
    )

    # Reddit returns [post_listing, comments_listing]
    if not isinstance(data, list) or len(data) < 2:
        return []

    comments_tree = data[1].get("data", {}).get("children", [])
    raw_comments: list[dict] = []
    for item in comments_tree:
        raw_comments.extend(_extract_comment_nodes(item))

    cleaned = clean_comment_records(raw_comments, max_comments=settings.COMMENT_LIMIT)
    logger.info(f"Fetched {len(cleaned)} comments for post {post_id}")
    return cleaned[:settings.COMMENT_LIMIT]
