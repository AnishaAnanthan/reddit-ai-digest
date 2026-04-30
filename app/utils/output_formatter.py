from datetime import datetime, timezone

from app.models.post_models import RankedPost


def format_top_posts_text(posts: list[RankedPost]) -> str:
    """
    Builds the final text output used by both console print and email body.
    """
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "Top 3 Reddit Finance Insights",
        "================================",
        f"Generated At: {generated_at}",
        "",
        "Top 3 Posts:",
        "------------",
        "",
    ]

    for idx, post in enumerate(posts, start=1):
        lines.append(f"{idx}.")
        lines.append(f"Title: {post.title}")
        lines.append(f"URL: {post.url}")
        lines.append(f"Summary: {post.summary}")
        lines.append("------------")
        lines.append("")

    return "\n".join(lines).strip() + "\n"