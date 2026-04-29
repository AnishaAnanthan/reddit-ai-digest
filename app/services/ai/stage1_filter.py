import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.config.settings import settings
from app.models.post_models import RawPost, Stage1Post
from app.services.ai.ai_client import ai_client
from app.utils.clean_comments import build_comment_summary, clean_comment_records, total_comment_char_count
from app.utils.validate_ai_output import validate_json_output

logger = logging.getLogger(__name__)

def _chunked(items: list[Any], size: int) -> list[list[Any]]:
    if size <= 0:
        return [items]
    return [items[index:index + size] for index in range(0, len(items), size)]


def _to_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y"}:
            return True
        if lowered in {"false", "0", "no", "n"}:
            return False
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _coerce_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _build_stage1_payload(post: RawPost) -> tuple[dict[str, Any], list]:
    cleaned_comments = clean_comment_records(post.comments, max_comments=settings.COMMENT_LIMIT)
    comment_summary = build_comment_summary(cleaned_comments, max_chars=settings.STAGE1_COMMENT_SUMMARY_CHAR_LIMIT)
    truncated_by_budget = total_comment_char_count(cleaned_comments) > settings.STAGE1_TOTAL_COMMENT_CHAR_BUDGET

    payload = {
        "post_id": post.post_id,
        "title": post.title,
        "content": post.content,
        "score": post.score,
        "subreddit": post.subreddit,
        "comment_count": len(cleaned_comments),
        "comments": [comment.model_dump() for comment in cleaned_comments],
        "comment_summary": comment_summary,
        "comment_truncated_by_budget": truncated_by_budget,
    }
    return payload, cleaned_comments


def _build_stage1_post(item: dict[str, Any], meta: dict[str, Any]) -> Stage1Post:
    legacy_keep = _to_bool(item.get("is_valuable"), _to_bool(item.get("keep"), False))
    is_valuable_post = _to_bool(item.get("is_valuable_post"), legacy_keep)
    is_valuable_comment = _to_bool(item.get("is_valuable_comment"), legacy_keep)
    discussion_complete = _to_bool(item.get("discussion_complete"), not _to_bool(item.get("involvement_needed"), False))

    comment_summary = _coerce_str(item.get("comment_summary"), meta.get("comment_summary", ""))
    discussion_incomplete_reason = _coerce_str(item.get("discussion_incomplete_reason"), "")
    reason = _coerce_str(item.get("reason"), "")
    category = _coerce_str(item.get("category"), "")

    actionable_comments = item.get("actionable_comments", [])
    if not isinstance(actionable_comments, list):
        actionable_comments = []

    stage1_post = Stage1Post(
        post_id=meta.get("post_id", ""),
        title=meta.get("title", item.get("title", "")),
        content=meta.get("content", ""),
        score=meta.get("score", 0),
        url=meta.get("url", ""),
        subreddit=meta.get("subreddit", ""),
        comments=meta.get("comments", []),
        is_valuable_post=is_valuable_post,
        is_valuable_comment=is_valuable_comment,
        discussion_complete=discussion_complete,
        discussion_incomplete_reason=discussion_incomplete_reason,
        comment_summary=comment_summary,
        is_valuable=is_valuable_post,
        keep=is_valuable_post,
        reason=reason,
        category=category,
        comment_assessment=_coerce_str(item.get("comment_assessment"), ""),
        involvement_needed=not discussion_complete,
        actionable_comments=actionable_comments,
    )

    if not stage1_post.comment_assessment:
        if stage1_post.is_valuable_comment:
            stage1_post.comment_assessment = "Comments are meaningful and support the post."
        else:
            stage1_post.comment_assessment = "Comments are weak, noisy, or not useful enough for strong discussion value."

    return stage1_post


async def _run_stage1_batch(subreddit: str, batch: list[RawPost], system_prompt: str) -> list[Stage1Post]:
    if not batch:
        return []

    post_meta: dict[str, dict[str, Any]] = {}
    ai_input_data: list[dict[str, Any]] = []

    for post in batch:
        payload, cleaned_comments = _build_stage1_payload(post)
        post_meta[post.post_id] = {
            "post_id": post.post_id,
            "title": post.title,
            "content": post.content,
            "url": post.url,
            "subreddit": post.subreddit,
            "score": post.score,
            "comments": cleaned_comments,
            "comment_summary": payload["comment_summary"],
        }
        ai_input_data.append(payload)

    user_content = json.dumps(
        {
            "subreddit": subreddit,
            "posts": ai_input_data,
        },
        indent=2,
    )
    logger.info(f"Sending {len(batch)} posts from r/{subreddit} to Stage 1 AI Filter.")

    max_retries = 2
    for attempt in range(max_retries):
        ai_output = await ai_client.call_ai(system_prompt, user_content)
        parsed_json = validate_json_output(ai_output)

        if parsed_json is None:
            logger.warning(
                f"Stage 1 AI output invalid for r/{subreddit}. Attempt {attempt + 1} of {max_retries}. Retrying..."
            )
            continue

        parsed_items_by_id: dict[str, dict[str, Any]] = {}
        parsed_items_by_title: dict[str, dict[str, Any]] = {}
        for item in parsed_json:
            if not isinstance(item, dict):
                continue
            post_id = _coerce_str(item.get("post_id"), "")
            title = _coerce_str(item.get("title"), "")
            if post_id:
                parsed_items_by_id[post_id] = item
            if title:
                parsed_items_by_title[title] = item

        stage1_posts: list[Stage1Post] = []
        for post in batch:
            item = parsed_items_by_id.get(post.post_id) or parsed_items_by_title.get(post.title) or {}
            stage1_posts.append(_build_stage1_post(item, post_meta[post.post_id]))

        logger.info(
            f"Stage 1 batch complete for r/{subreddit}. Kept {sum(1 for post in stage1_posts if post.keep)} posts from {len(batch)} evaluated posts."
        )
        return stage1_posts

    logger.error(f"Stage 1 AI filtering failed for r/{subreddit} after retries. Falling back to deterministic heuristics.")

    fallback_posts: list[Stage1Post] = []
    for post in batch:
        meta = post_meta[post.post_id]
        comment_count = len(meta.get("comments", []))
        comment_char_count = total_comment_char_count(meta.get("comments", []))
        is_valuable_post = post.score > 0 or len((post.title or "") + (post.content or "")) > 120
        is_valuable_comment = comment_count >= 2 and comment_char_count > 120
        fallback_posts.append(
            Stage1Post(
                post_id=meta.get("post_id", ""),
                title=meta.get("title", ""),
                content=meta.get("content", ""),
                score=meta.get("score", 0),
                url=meta.get("url", ""),
                subreddit=meta.get("subreddit", ""),
                comments=meta.get("comments", []),
                is_valuable_post=is_valuable_post,
                is_valuable_comment=is_valuable_comment,
                discussion_complete=is_valuable_comment,
                discussion_incomplete_reason="Invalid AI response; fell back to heuristic discussion assessment.",
                comment_summary=meta.get("comment_summary", ""),
                is_valuable=is_valuable_post,
                keep=is_valuable_post,
                reason="Fallback selection used after invalid AI response.",
                category="framework" if is_valuable_post and is_valuable_comment else "noise",
                comment_assessment=(
                    "Heuristic fallback marked the discussion as useful."
                    if is_valuable_comment
                    else "Heuristic fallback marked the discussion as weak or incomplete."
                ),
                involvement_needed=False,
                actionable_comments=[],
            )
        )

    return fallback_posts


async def filter_posts(posts: list[RawPost], return_diagnostics: bool = False):
    """
    Runs Stage 1 AI filtering on raw posts.
    """
    if not posts:
        return ([], {}) if return_diagnostics else []

    prompt_path = Path(__file__).resolve().parent / "prompts" / "filter_prompt.txt"
    with prompt_path.open("r", encoding="utf-8") as f:
        system_prompt = f.read()

    grouped_posts: dict[str, list[RawPost]] = defaultdict(list)
    for post in posts:
        grouped_posts[post.subreddit or ""] .append(post)

    selected_posts: list[Stage1Post] = []
    diagnostics = {
        "total_raw_posts": len(posts),
        "stage1_evaluated_posts": 0,
        "post_plus_comment_kept": 0,
        "post_only_fallback_kept": 0,
        "dropped_due_to_comment_noise": 0,
        "discussion_complete_count": 0,
        "discussion_incomplete_count": 0,
        "stage1_by_subreddit": {subreddit: 0 for subreddit in grouped_posts.keys()},
    }

    for subreddit, subreddit_posts in grouped_posts.items():
        subreddit_stage1: list[Stage1Post] = []
        for batch in _chunked(subreddit_posts, settings.STAGE1_BATCH_SIZE):
            subreddit_stage1.extend(await _run_stage1_batch(subreddit, batch, system_prompt))

        diagnostics["stage1_evaluated_posts"] += len(subreddit_stage1)
        diagnostics["discussion_complete_count"] += sum(1 for post in subreddit_stage1 if post.discussion_complete)
        diagnostics["discussion_incomplete_count"] += sum(1 for post in subreddit_stage1 if not post.discussion_complete)

        tier_a = [post for post in subreddit_stage1 if post.is_valuable_post and post.is_valuable_comment]
        if tier_a:
            kept = tier_a
            diagnostics["post_plus_comment_kept"] += len(kept)
            diagnostics["dropped_due_to_comment_noise"] += sum(
                1 for post in subreddit_stage1 if post.is_valuable_post and not post.is_valuable_comment
            )
        else:
            kept = [post for post in subreddit_stage1 if post.is_valuable_post]
            diagnostics["post_only_fallback_kept"] += len(kept)
            diagnostics["dropped_due_to_comment_noise"] += sum(
                1 for post in subreddit_stage1 if not post.is_valuable_post
            )

        diagnostics["stage1_by_subreddit"][subreddit] = len(kept)
        selected_posts.extend(kept)

    logger.info(
        "Stage 1 filtering complete. Kept %s posts across %s subreddits.",
        len(selected_posts),
        len(grouped_posts),
    )

    if return_diagnostics:
        return selected_posts, diagnostics
    return selected_posts
