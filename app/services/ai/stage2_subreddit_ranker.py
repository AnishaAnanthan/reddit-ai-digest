import json
import logging
from pathlib import Path

from app.models.post_models import RankedPost, RawPost
from app.services.ai.ai_client import ai_client
from app.utils.validate_ai_output import validate_top_posts_output

logger = logging.getLogger(__name__)

async def rank_subreddit_posts(subreddit: str, posts: list[RawPost]) -> list[RankedPost]:
    """
    Ranks fresh posts for a single subreddit using composite importance (popularity + comments).
    """
    if not posts:
        return []

    prompt_path = Path(__file__).resolve().parent / "prompts" / "subreddit_ranking_prompt.txt"
    with prompt_path.open("r", encoding="utf-8") as f:
        system_prompt = f.read()

    ai_input = []
    for post in posts:
        # Extract top comment bodies for analysis
        comment_texts = [c.body for c in post.comments[:5] if not c.is_deleted and not c.is_removed]
        comment_summary = " | ".join(comment_texts) if comment_texts else "No comments yet."
        
        ai_input.append(
            {
                "post_id": post.post_id,
                "title": post.title,
                "score": post.score,
                "url": post.url,
                "content_preview": post.content[:200], # First 200 chars
                "comment_summary": comment_summary,
            }
        )

    user_content = json.dumps(
        {
            "subreddit": subreddit,
            "posts": ai_input,
        },
        indent=2,
    )

    logger.info(f"Running v2 composite ranking for r/{subreddit} with {len(posts)} posts.")

    max_retries = 2
    for attempt in range(max_retries):
        ai_output = await ai_client.call_ai(system_prompt, user_content)
        parsed = validate_top_posts_output(ai_output)

        if parsed is not None:
            # We no longer slice [:3] here, we return what the AI ranked as important
            # Inject subreddit name for each post
            for item in parsed:
                item["subreddit"] = subreddit
            return [RankedPost(**item) for item in parsed]

        logger.warning(
            f"Subreddit ranking output invalid for r/{subreddit}. Attempt {attempt + 1} of {max_retries}."
        )

    logger.error(f"Subreddit ranking failed for r/{subreddit} after retries.")
    return []