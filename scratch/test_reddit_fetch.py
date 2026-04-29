import asyncio
import logging
from app.services.reddit.reddit_client import reddit_get

# Setup logging to see what's happening
logging.basicConfig(level=logging.INFO)

async def test_raw_fetch():
    print("Testing reddit_get for r/IndiaInvestments...")
    path = "/r/IndiaInvestments/top.json"
    params = {"limit": 5, "t": "day"}
    
    result = await reddit_get(path, params=params)
    
    if result and "data" in result:
        print("SUCCESS: Received data from Reddit.")
        print(f"Number of posts: {len(result['data']['children'])}")
    else:
        print("FAILED: No data received. Check if blocked.")

if __name__ == "__main__":
    asyncio.run(test_raw_fetch())
