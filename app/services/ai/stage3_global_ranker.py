import json
import logging
from pathlib import Path

from app.models.post_models import RankedPost
from app.services.ai.ai_client import ai_client
from app.utils.validate_ai_output import validate_top_posts_output

logger = logging.getLogger(__name__)


async def rank_global_posts(posts: list[RankedPost]) -> list[RankedPost]:
    """
    Ranks merged shortlisted posts from all subreddits and returns final top posts.
    """
    if not posts:
        return []

    prompt_path = Path(__file__).resolve().parent / "prompts" / "global_ranking_prompt.txt"
    with prompt_path.open("r", encoding="utf-8") as f:
        system_prompt = f.read()

    user_content = json.dumps(
        {
            "posts": [post.model_dump() for post in posts],
        },
        indent=2,
    )

    logger.info(f"Running global ranking for {len(posts)} merged posts.")

    max_retries = 2
    for attempt in range(max_retries):
        ai_output = await ai_client.call_ai(system_prompt, user_content)
        parsed = validate_top_posts_output(ai_output)

        if parsed is not None:
            ranked = [RankedPost(**item) for item in parsed]
            return ranked[:3]

        logger.warning(f"Global ranking output invalid. Attempt {attempt + 1} of {max_retries}.")

    logger.error("Global ranking failed after retries.")
    return []