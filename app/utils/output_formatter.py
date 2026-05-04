from datetime import datetime, timezone, timedelta

from app.models.post_models import RankedPost

def format_top_posts_text(posts: list[RankedPost]) -> str:
    """
    Builds the final text output used by both console print and email body.
    v2: Includes Importance Score. Returns a proper message if no posts found.
    """
    # Get UTC time and adjust to IST (UTC + 5:30)
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    timestamp = ist_now.strftime("%Y-%m-%d %H:%M IST")
    
    header = f"Reddit AI Agent: Today's High-Importance Digest\n"
    header += f"===============================================\n"
    header += f"Generated At: {timestamp}\n\n"
    
    lines = [
        header.strip(),
        "",
    ]
    
    # Handle empty posts case
    if not posts:
        lines.append("No Posts Found")
        lines.append("-" * 30)
        lines.append("")
        lines.append("No high-importance posts were found in the monitored subreddits for today.")
        lines.append("Check back later for the next update.")
        return "\n".join(lines).strip() + "\n"
    
    # Sort posts by importance score descending
    posts = sorted(posts, key=lambda x: x.importance_score, reverse=True)
    
    lines.append("Ranked Signal Summary:")
    lines.append("----------------------")
    lines.append("")

    for idx, post in enumerate(posts, start=1):
        lines.append(f"{idx}. {post.title} [r/{post.subreddit}]")
        lines.append(f"   [Importance Score: {post.importance_score}/10.0] | [Status: {post.discussion_status}]")
        lines.append(f"   URL: {post.url}")
        lines.append(f"   Summary: {post.summary}")
        lines.append("   ------------------------------------------------")
        lines.append("")

    return "\n".join(lines).strip() + "\n"