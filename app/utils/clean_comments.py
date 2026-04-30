from __future__ import annotations

import re
from typing import Any

from app.config.settings import settings
from app.models.post_models import CommentRecord

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_WHITESPACE_RE = re.compile(r"\s+")

_NOISE_PHRASES = {
    "thanks",
    "thank you",
    "thx",
    "nice post",
    "good post",
    "good question",
    "great post",
    "following",
    "same",
    "agreed",
    "i agree",
    "lol",
    "haha",
    "hello",
    "hi",
    "hey",
    "upvoted",
}


def _normalize_text(text: str) -> str:
    if not text:
        return ""
    text = text.replace("\u200b", " ")
    text = _URL_RE.sub("", text)
    text = _WHITESPACE_RE.sub(" ", text)
    return text.strip()


def _is_noise_comment(text: str, author: str = "") -> bool:
    lowered = text.lower().strip()
    if not lowered:
        return True
    if lowered in {"[deleted]", "[removed]"}:
        return True
    if len(lowered) < 12:
        return True
    if author and "bot" in author.lower():
        return True
    if any(phrase == lowered for phrase in _NOISE_PHRASES):
        return True
    if lowered.startswith("i agree") or lowered.startswith("thanks"):
        return True
    if lowered.endswith("?") and len(lowered.split()) <= 3:
        return True
    return False


def clean_comment_text(text: str) -> str:
    """Normalizes a single comment body."""
    return _normalize_text(text)


def is_meaningful_comment(text: str) -> bool:
    """Checks if a normalized comment is likely substantive."""
    if not text:
        return False
    if _is_noise_comment(text):
        return False
    return len(text) > 20 or len(text.split()) >= 5


def clean_comments(raw_comments: list[str]) -> list[str]:
    """Filters and cleans a list of raw comment strings."""
    cleaned: list[str] = []
    seen: set[str] = set()

    for comment in raw_comments:
        c_text = clean_comment_text(comment)
        if not is_meaningful_comment(c_text):
            continue
        key = c_text.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(c_text[: settings.STAGE1_COMMENT_CHAR_LIMIT])

    return cleaned


def clean_comment_records(raw_comments: list[Any], max_comments: int | None = None) -> list[CommentRecord]:
    """Cleans a list of structured or string comments into CommentRecord models."""
    normalized_comments = [CommentRecord.from_any(raw_comment) for raw_comment in raw_comments]
    normalized_comments.sort(key=lambda item: item.score, reverse=True)

    cleaned: list[CommentRecord] = []
    seen: set[str] = set()
    max_comments = max_comments or settings.COMMENT_LIMIT

    for comment in normalized_comments:
        body = clean_comment_text(comment.body)
        if not is_meaningful_comment(body):
            continue
        if comment.is_deleted or comment.is_removed:
            continue
        key = body.lower()
        if key in seen:
            continue
        seen.add(key)
        cleaned.append(
            CommentRecord(
                body=body[: settings.STAGE1_COMMENT_CHAR_LIMIT],
                score=comment.score,
                author=comment.author,
                is_deleted=comment.is_deleted,
                is_removed=comment.is_removed,
                permalink=comment.permalink,
            )
        )
        if len(cleaned) >= max_comments:
            break

    return cleaned[:max_comments]


def build_comment_summary(comments: list[CommentRecord], max_chars: int | None = None) -> str:
    """Builds a compact comment summary for Stage 1 and ranking stages."""
    max_chars = max_chars or settings.STAGE1_COMMENT_SUMMARY_CHAR_LIMIT
    if not comments:
        return "No meaningful comments after cleaning."

    parts: list[str] = []
    total_chars = 0
    for idx, comment in enumerate(comments, start=1):
        snippet = comment.body.strip()
        if len(snippet) > 180:
            snippet = snippet[:177].rstrip() + "..."
        piece = f"{idx}. {snippet}"
        if total_chars + len(piece) + 2 > max_chars:
            break
        parts.append(piece)
        total_chars += len(piece) + 2

    summary = " | ".join(parts)
    if not summary:
        summary = comments[0].body[:max_chars]
    return summary[:max_chars]


def total_comment_char_count(comments: list[CommentRecord]) -> int:
    return sum(len(comment.body) for comment in comments)
