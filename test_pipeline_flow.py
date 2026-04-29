import asyncio
from collections import defaultdict

from app.config.settings import settings
from app.models.post_models import RawPost, RankedPost
from app.services.ai.stage1_filter import filter_posts
from app.services.ai.stage2_subreddit_ranker import rank_subreddit_posts
from app.services.ai.stage3_global_ranker import rank_global_posts
from app.services.reddit.fetch_comments import fetch_comments_for_post
from app.services.reddit.reddit_client import reddit_get
from app.utils.output_formatter import format_top_posts_text


def ask_for_forums() -> list[str]:
    print("Enter subreddit/forum names separated by commas.")
    print(f"Default configured forums: {', '.join(settings.SUBREDDITS)}")
    user_input = input("Forums (press Enter for default): ").strip()

    if not user_input:
        return settings.SUBREDDITS

    forums = []
    for item in user_input.split(","):
        forum = item.strip().lstrip("r/").strip()
        if forum:
            forums.append(forum)

    return forums or settings.SUBREDDITS


async def fetch_posts_for_forums(forums: list[str]) -> list[RawPost]:
    all_posts: list[RawPost] = []

    for subreddit in forums:
        print(f"\nFetching raw posts for r/{subreddit}...")
        data = await reddit_get(
            f"/r/{subreddit}/top.json",
            params={"limit": settings.POST_LIMIT, "t": "day"},
        )

        children = data.get("data", {}).get("children", []) if isinstance(data, dict) else []
        if not children:
            print(f"  No posts returned for r/{subreddit}.")
            continue

        print(f"  Found {len(children)} raw posts.")

        for item in children:
            post_data = item.get("data", {})
            post_id = post_data.get("id", "")
            permalink = post_data.get("permalink", "")

            comments = await fetch_comments_for_post(post_id, subreddit)

            all_posts.append(
                RawPost(
                    post_id=post_id,
                    title=post_data.get("title", ""),
                    content=post_data.get("selftext", ""),
                    score=post_data.get("score", 0),
                    url=f"https://www.reddit.com{permalink}",
                    subreddit=subreddit,
                    comments=comments,
                )
            )

    return all_posts


def print_raw_posts(posts: list[RawPost]) -> None:
    print("\n====================")
    print("RAW POSTS")
    print("====================")
    if not posts:
        print("No raw posts fetched.")
        return

    grouped = defaultdict(list)
    for post in posts:
        grouped[post.subreddit].append(post)

    for subreddit, items in grouped.items():
        print(f"\nr/{subreddit} - {len(items)} posts")
        for idx, post in enumerate(items, start=1):
            print(f"{idx}. {post.title}")
            print(f"   Score: {post.score}")
            print(f"   URL: {post.url}")


def print_stage1_posts(posts) -> None:
    print("\n====================")
    print("STAGE 1 - FILTERED POSTS")
    print("====================")
    if not posts:
        print("No posts survived Stage 1 filtering.")
        return

    grouped = defaultdict(list)
    for post in posts:
        grouped[post.subreddit].append(post)

    for subreddit, items in grouped.items():
        print(f"\nr/{subreddit} - {len(items)} posts")
        for idx, post in enumerate(items, start=1):
            print(f"{idx}. {post.title}")
            print(f"   Score: {post.score}")
            print(f"   Category: {post.category}")
            print(f"   Reason: {post.reason}")
            print(f"   Discussion Complete: {post.discussion_complete}")
            print(f"   Is Valuable Post: {post.is_valuable_post}")
            print(f"   Is Valuable Comment: {post.is_valuable_comment}")


def print_stage1_diagnostics(diagnostics: dict) -> None:
    print("\n====================")
    print("STAGE 1 - DIAGNOSTICS")
    print("====================")
    print(f"Total raw posts: {diagnostics.get('total_raw_posts', 0)}")
    print(f"Posts evaluated: {diagnostics.get('stage1_evaluated_posts', 0)}")
    print(f"Tier A (post + comments valuable): {diagnostics.get('post_plus_comment_kept', 0)}")
    print(f"Tier B (post-only valuable): {diagnostics.get('post_only_fallback_kept', 0)}")
    print(f"Dropped (comment noise): {diagnostics.get('dropped_due_to_comment_noise', 0)}")
    print(f"Discussion complete: {diagnostics.get('discussion_complete_count', 0)}")
    print(f"Discussion incomplete: {diagnostics.get('discussion_incomplete_count', 0)}")
    print(f"\nBy subreddit:")
    for subreddit, count in diagnostics.get('stage1_by_subreddit', {}).items():
        print(f"  r/{subreddit}: {count} posts kept")


def print_stage2_rankings(rankings: dict[str, list[RankedPost]]) -> None:
    print("\n====================")
    print("STAGE 2 - SUBREDDIT RANKING")
    print("====================")
    if not rankings:
        print("No subreddit rankings were produced.")
        return

    for subreddit, posts in rankings.items():
        print(f"\nr/{subreddit} - {len(posts)} ranked posts")
        if not posts:
            print("  No ranked posts for this subreddit.")
            continue
        for idx, post in enumerate(posts, start=1):
            print(f"{idx}. {post.title}")
            print(f"   URL: {post.url}")
            print(f"   Summary: {post.summary}")


async def main() -> None:
    forums = ask_for_forums()
    print(f"\nSelected forums: {', '.join(forums)}")

    raw_posts = await fetch_posts_for_forums(forums)
    print_raw_posts(raw_posts)

    if not raw_posts:
        print("\nNo raw posts fetched. Stopping.")
        return

    stage1_posts, stage1_diagnostics = await filter_posts(raw_posts, return_diagnostics=True)
    print_stage1_posts(stage1_posts)
    print_stage1_diagnostics(stage1_diagnostics)

    if not stage1_posts:
        print("\nNo posts survived Stage 1. Stopping.")
        return

    posts_by_subreddit: dict[str, list] = defaultdict(list)
    for post in stage1_posts:
        posts_by_subreddit[post.subreddit].append(post)

    stage2_rankings: dict[str, list[RankedPost]] = {}
    merged_posts: list[RankedPost] = []

    for subreddit in forums:
        ranked_posts = await rank_subreddit_posts(subreddit, posts_by_subreddit.get(subreddit, []))
        stage2_rankings[subreddit] = ranked_posts
        merged_posts.extend(ranked_posts)

    print_stage2_rankings(stage2_rankings)

    if not merged_posts:
        print("\nNo posts survived Stage 2. Stopping.")
        return

    final_posts = await rank_global_posts(merged_posts)

    print("\n====================")
    print("STAGE 3 - GLOBAL RANKING")
    print("====================")
    if not final_posts:
        print("No final posts returned from global ranking.")
        return

    print(format_top_posts_text(final_posts))


if __name__ == "__main__":
    asyncio.run(main())