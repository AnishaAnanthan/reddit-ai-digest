from fastapi import FastAPI
import httpx
import asyncio
import logging
import time
from app.services.reddit.fetch_posts import fetch_top_posts
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
    
    # Parse the time from settings (format HH:MM)
    try:
        hour, minute = map(int, settings.PIPELINE_SCHEDULE_TIME.split(":"))
        scheduler.add_job(
            run_full_ranking_pipeline,
            "cron",
            hour=hour,
            minute=minute,
            id="reddit_ranking_job"
        )
        scheduler.start()
        logger.info(f">>> Pipeline scheduled to run daily at {settings.PIPELINE_SCHEDULE_TIME}")
    except Exception as e:
        logger.error(f">>> Failed to schedule pipeline: {e}")

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
    """
    all_raw_data = {}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        for subreddit in settings.SUBREDDITS:
            url = f"https://www.reddit.com/r/{subreddit}/top.json?limit={settings.POST_LIMIT}&t=day"
            try:
                response = await client.get(url, headers=headers, follow_redirects=True)
                if response.status_code == 200:
                    all_raw_data[subreddit] = response.json()
                else:
                    all_raw_data[subreddit] = {"error": f"Status code {response.status_code}"}
            except Exception as e:
                all_raw_data[subreddit] = {"error": str(e)}
                
    return {"status": "success", "data": all_raw_data}

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
