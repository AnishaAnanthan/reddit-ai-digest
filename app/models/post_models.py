from typing import Any, List

from pydantic import BaseModel, Field, field_validator


class CommentRecord(BaseModel):
    body: str = ""
    score: int = 0
    author: str = ""
    is_deleted: bool = False
    is_removed: bool = False
    permalink: str = ""

    @classmethod
    def from_any(cls, value: Any) -> "CommentRecord":
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            return cls(body=value)
        if isinstance(value, dict):
            return cls(
                body=str(value.get("body", "")),
                score=int(value.get("score", 0) or 0),
                author=str(value.get("author", "") or ""),
                is_deleted=bool(value.get("is_deleted", False)),
                is_removed=bool(value.get("is_removed", False)),
                permalink=str(value.get("permalink", "") or ""),
            )
        return cls(body=str(value))

# --- Raw Reddit Data Models ---
class RawPost(BaseModel):
    post_id: str
    title: str
    content: str
    score: int
    url: str
    subreddit: str = ""
    created_utc: float = 0.0
    comments: List[CommentRecord] = Field(default_factory=list)

    @field_validator("comments", mode="before")
    @classmethod
    def _coerce_comments(cls, value: Any) -> List[CommentRecord]:
        if not value:
            return []
        return [CommentRecord.from_any(item) for item in value]

# --- Stage 1 Filter Data Models ---
class Stage1Post(BaseModel):
    post_id: str = ""
    title: str
    content: str
    score: int = 0
    url: str = ""
    subreddit: str = ""
    comments: List[CommentRecord] = Field(default_factory=list)
    is_valuable_post: bool = False
    is_valuable_comment: bool = False
    discussion_complete: bool = False
    discussion_incomplete_reason: str = ""
    comment_summary: str = ""
    is_valuable: bool = False
    keep: bool = False
    reason: str = ""
    category: str = ""
    comment_assessment: str = ""
    involvement_needed: bool = False
    actionable_comments: List[str] = Field(default_factory=list)

    @field_validator("comments", mode="before")
    @classmethod
    def _coerce_comments(cls, value: Any) -> List[CommentRecord]:
        if not value:
            return []
        return [CommentRecord.from_any(item) for item in value]


class RankedPost(BaseModel):
    title: str
    url: str
    summary: str
    importance_score: float = 0.0
    reasoning: str = ""
    discussion_status: str = ""
