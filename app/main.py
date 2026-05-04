from fastapi import FastAPI, Response
import logging
import time
import asyncio
from zoneinfo import ZoneInfo
from app.services.reddit.fetch_posts import fetch_top_posts
from app.services.ai.stage2_subreddit_ranker import rank_subreddit_posts
from app.services.pipeline_service import run_full_ranking_pipeline
from app.services.notifications.email_sender import send_results_email
from app.utils.output_formatter import format_top_posts_text
from app.config.settings import settings
from app.models.post_models import RankedPost
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from contextlib import asynccontextmanager

# Configure root logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize and start scheduler
    scheduler = AsyncIOScheduler(timezone=ZoneInfo("Asia/Kolkata"))
    
    try:
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
        logger.info(">>> Scheduler started successfully")
    except Exception as e:
        logger.error(f">>> Failed to initialize scheduler: {e}", exc_info=True)

    yield
    # Shutdown
    try:
        scheduler.shutdown()
        logger.info(">>> Scheduler shut down successfully")
    except Exception as e:
        logger.error(f">>> Failed to shutdown scheduler: {e}")

app = FastAPI(
    title="Reddit AI Agent v2",
    description="Automated Reddit intelligence agent with composite importance ranking.",
    lifespan=lifespan
)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "time": time.time()}

# --- TEST ENDPOINTS FOR EACH STEP ---

@app.get("/test/fetch")
async def test_fetch():
    """
    STEP 1: Fetching (Multi-Category + 24h Filter)
    """
    posts = await fetch_top_posts()
    return {
        "step": "1 - Fetching",
        "description": "Multi-category scan with 24-hour timestamp filter.",
        "count": len(posts),
        "data": posts
    }

@app.get("/test/rank")
async def test_rank():
    """
    STEP 2: Ranking + STEP 3: Email Notification
    Processes ALL subreddits, ranks them, and SENDS an email.
    """
    logger.info(">>> /test/rank: Starting full ranking test with email...")
    raw_posts = await fetch_top_posts()
    if not raw_posts:
        return {"error": "No fresh posts found to rank."}
    
    results = {}
    all_ranked_objects = []
    
    for subreddit in settings.SUBREDDITS:
        subreddit_posts = [p for p in raw_posts if p.subreddit == subreddit]
        if not subreddit_posts:
            results[subreddit] = "No posts from last 24h"
            continue
            
        ranked_list = await rank_subreddit_posts(subreddit, subreddit_posts)
        
        # Deduplicate AI output and convert to models
        unique_ranked = []
        seen_urls = set()
        for p in ranked_list:
            if p.url not in seen_urls:
                all_ranked_objects.append(p)
                unique_ranked.append(p.model_dump())
                seen_urls.add(p.url)
        
        results[subreddit] = {
            "input_count": len(subreddit_posts),
            "ranked_count": len(unique_ranked),
            "data": unique_ranked
        }
    
    # Send the email notification
    email_status = "Skipped (no posts)"
    if all_ranked_objects:
        logger.info(f">>> /test/rank: Sending email for {len(all_ranked_objects)} posts...")
        final_text = format_top_posts_text(all_ranked_objects)
        try:
            # send_results_email is a blocking function, run in thread
            await asyncio.to_thread(send_results_email, final_text)
            email_status = "Sent Successfully"
        except Exception as e:
            logger.error(f"Email failed: {e}")
            email_status = f"Failed: {str(e)}"

    return {
        "step": "2 & 3 - Ranking and Emailing",
        "total_subreddits": len(settings.SUBREDDITS),
        "email_status": email_status,
        "results": results
    }

@app.get("/test/format")
async def test_format():
    """
    STEP 3: Formatting (Email Preview)
    """
    raw_posts = await fetch_top_posts()
    if not raw_posts:
        return Response(content="No fresh posts found to format.", media_type="text/plain")
        
    subreddit = settings.SUBREDDITS[0]
    subreddit_posts = [p for p in raw_posts if p.subreddit == subreddit]
    ranked = await rank_subreddit_posts(subreddit, subreddit_posts)
    
    formatted_text = format_top_posts_text(ranked)
    return Response(content=formatted_text, media_type="text/plain")

@app.get("/test/raw-count")
async def test_raw_count():
    raw_posts = await fetch_top_posts()
    return {
        "final_valid_posts": len(raw_posts),
        "subreddits": settings.SUBREDDITS
    }

# --- FULL PIPELINE ENDPOINTS ---

@app.post("/run-ranking-pipeline")
async def run_ranking_pipeline_endpoint():
    return await run_full_ranking_pipeline()

@app.get("/todays-highlights")
async def get_todays_highlights():
    return await run_full_ranking_pipeline()
