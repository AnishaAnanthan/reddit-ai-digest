import json
import logging
from pathlib import Path

from app.models.post_models import RankedPost, Stage1Post
from app.services.ai.ai_client import ai_client
from app.utils.validate_ai_output import validate_top_posts_output

logger = logging.getLogger(__name__)


async def rank_subreddit_posts(subreddit: str, posts: list[Stage1Post]) -> list[RankedPost]:
    """
    Ranks already-validated posts for a single subreddit and returns top posts.
    """
    if not posts:
        return []

    prompt_path = Path(__file__).resolve().parent / "prompts" / "subreddit_ranking_prompt.txt"
    with prompt_path.open("r", encoding="utf-8") as f:
        system_prompt = f.read()

    ai_input = []
    for post in posts:
        ai_input.append(
            {
                "title": post.title,
                "score": post.score,
                "url": post.url,
                "reason": post.reason,
                "category": post.category,
                "is_valuable_post": post.is_valuable_post,
                "is_valuable_comment": post.is_valuable_comment,
                "discussion_complete": post.discussion_complete,
                "comment_summary": post.comment_summary,
            }
        )

    user_content = json.dumps(
        {
            "subreddit": subreddit,
            "posts": ai_input,
        },
        indent=2,
    )

    logger.info(f"Running subreddit ranking for r/{subreddit} with {len(posts)} validated posts.")

    max_retries = 2
    for attempt in range(max_retries):
        ai_output = await ai_client.call_ai(system_prompt, user_content)
        parsed = validate_top_posts_output(ai_output)

        if parsed is not None:
            ranked = [RankedPost(**item) for item in parsed]
            return ranked[:3]

        logger.warning(
            f"Subreddit ranking output invalid for r/{subreddit}. Attempt {attempt + 1} of {max_retries}."
        )

    logger.error(f"Subreddit ranking failed for r/{subreddit} after retries.")
    return []