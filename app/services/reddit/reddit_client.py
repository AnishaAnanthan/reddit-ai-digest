import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)

BASE_URL = "https://www.reddit.com"

# Browser User-Agent works better than bot UA for Reddit's public JSON endpoints
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.reddit.com/",
}

# Allow up to 3 concurrent Reddit requests — enough parallelism without triggering 429
_request_semaphore = asyncio.Semaphore(3)

async def reddit_get(path: str, params: dict = None) -> dict | list:
    """
    Makes a GET request to Reddit's public JSON API.
    Uses a semaphore to limit concurrency and exponential backoff on 429.
    `path` example: '/r/FIRE_IND/top.json'
    """
    if params is None:
        params = {}
    params["raw_json"] = 1  # Prevents Reddit from HTML-encoding characters

    url = f"{BASE_URL}{path}"
    max_retries = 3

    async with _request_semaphore:
        async with httpx.AsyncClient(headers=HEADERS, follow_redirects=True) as client:
            for attempt in range(max_retries + 1):
                try:
                    logger.debug(f"GET {url} (attempt {attempt + 1})")
                    response = await client.get(url, params=params, timeout=15.0)

                    if response.status_code == 403:
                        logger.warning(f"403 Blocked for {url} — subreddit may be private or restricted.")
                        return {}

                    if response.status_code == 429:
                        wait = 5 * (2 ** attempt)  # 5s, 10s, 20s
                        logger.warning(f"429 Rate limited for {url}. Waiting {wait}s (attempt {attempt + 1}/{max_retries + 1})...")
                        await asyncio.sleep(wait)
                        continue

                    response.raise_for_status()
                    return response.json()

                except httpx.HTTPStatusError as e:
                    logger.error(f"HTTP error for {url}: {e}")
                    return {}
                except Exception as e:
                    logger.error(f"Request failed for {url}: {e}")
                    return {}

    logger.error(f"All retries exhausted for {url}")
    return {}
