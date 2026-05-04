from fastapi import FastAPI
import httpx
import asyncio
import logging
import time
from app.services.reddit.fetch_posts import fetch_top_posts
from app.services.reddit.reddit_client import reddit_get
from app.services.ai.stage1_filter import filter_posts
from app.services.ai.stage2_subreddit_ranker import rank_subreddit_posts
from app.services.ai.stage3_global_ranker import rank_global_posts
from app.services.notifications.email_sender import send_results_email
from app.utils.output_formatter import format_top_posts_text
from app.config.settings import settings
from app.services.pipeline_service import run_full_ranking_pipeline
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

# Configure root logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and start scheduler
    scheduler = AsyncIOScheduler()
    
    # Parse the times from settings (format HH:MM,HH:MM,HH:MM)
    times = settings.PIPELINE_SCHEDULE_TIME.split(",")
    for t in times:
        try:
            hour, minute = map(int, t.strip().split(":"))
            scheduler.add_job(
                run_full_ranking_pipeline,
                "cron",
                hour=hour,
                minute=minute,
                id=f"reddit_ranking_job_{hour}_{minute}"
            )
            logger.info(f">>> Pipeline scheduled to run daily at {t.strip()}")
        except Exception as e:
            logger.error(f">>> Failed to schedule pipeline for time {t}: {e}")
    
    scheduler.start()

    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(
    title="Reddit AI Digest - Stage 1",
    description="API to fetch and filter Reddit posts.",
    lifespan=lifespan
)

@app.get("/raw-posts")
async def get_parsed_raw_posts():
    """
    Fetches the posts and returns them parsed into our standard RawPost models.
    """
    posts = await fetch_top_posts()
    return {"status": "success", "count": len(posts), "data": posts}

@app.get("/filtered-posts")
async def get_filtered_posts():
    """
    Fetches top posts from all configured subreddits and runs them through
    the Stage 1 AI filter. Returns only meaningful discussions, with Reddit
    URLs and subreddit names included.
    """
    t0 = time.time()
    print(">>> /filtered-posts: Fetching raw posts from Reddit...", flush=True)
    raw_posts = await fetch_top_posts()
    t1 = time.time()
    print(f">>> /filtered-posts: Fetched {len(raw_posts)} posts in {t1-t0:.1f}s", flush=True)

    if not raw_posts:
        return {"status": "error", "message": "No posts fetched from Reddit."}

    print(f">>> /filtered-posts: Sending {len(raw_posts)} posts to AI filter...", flush=True)
    filtered_posts, diagnostics = await filter_posts(raw_posts, return_diagnostics=True)
    t2 = time.time()
    print(f">>> /filtered-posts: AI filter done in {t2-t1:.1f}s — kept {len(filtered_posts)} posts", flush=True)
    print(f">>> /filtered-posts: Total time: {t2-t0:.1f}s", flush=True)

    return {
        "status": "success",
        "count": len(filtered_posts),
        "stage1_diagnostics": diagnostics,
        "data": [post.model_dump() for post in filtered_posts]
    }

@app.get("/reddit-raw-json")
async def get_reddit_raw_json():
    """
    Fetches the EXACT raw JSON from Reddit's API (unparsed) for all configured subreddits.
    Uses our centralized reddit_get utility to avoid 403 blocks.
    """
    all_raw_data = {}
    
    # Run requests concurrently for efficiency
    tasks = []
    for subreddit in settings.SUBREDDITS:
        path = f"/r/{subreddit}/top.json"
        params = {"limit": settings.POST_LIMIT, "t": "day"}
        tasks.append(reddit_get(path, params=params))
    
    results = await asyncio.gather(*tasks)
    
    total_posts = 0
    for subreddit, result in zip(settings.SUBREDDITS, results):
        if not result:
            all_raw_data[subreddit] = {"error": "Failed to fetch data (likely blocked or rate limited)"}
        else:
            all_raw_data[subreddit] = result
            # Count the number of children (posts) in this subreddit
            post_count = len(result.get("data", {}).get("children", []))
            total_posts += post_count
            logger.info(f"Fetched {post_count} raw posts from r/{subreddit}")
                
    logger.info(f"Total raw posts fetched across all subreddits: {total_posts}")
    return {
        "status": "success", 
        "total_posts_fetched": total_posts,
        "data": all_raw_data
    }

@app.post("/run-stage1")
async def run_stage1_filter():
    """
    Fetches the raw posts and runs them through the Stage 1 AI Filter.
    Returns only the meaningful discussions.
    """
    raw_posts = await fetch_top_posts()
    
    if not raw_posts:
        return {"status": "error", "message": "No posts fetched from Reddit."}
        
    filtered_posts, diagnostics = await filter_posts(raw_posts, return_diagnostics=True)
    return {
        "status": "success",
        "count": len(filtered_posts),
        "stage1_diagnostics": diagnostics,
        "data": [post.model_dump() for post in filtered_posts]
    }


@app.post("/run-ranking-pipeline")
async def run_ranking_pipeline():
    """
    Manually trigger the full ranking flow.
    """
    return await run_full_ranking_pipeline()
