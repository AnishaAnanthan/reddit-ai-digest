import asyncio
import httpx
import json

SUBREDDITS = [
    "indiainvestments",
    "FIRE_IND",
    "personalfinanceindia"
]

async def fetch_raw_json():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        for subreddit in SUBREDDITS:
            url = f"https://www.reddit.com/r/{subreddit}/top.json?limit=100&t=day"
            print(f"\n--- Fetching {subreddit} ---")
            try:
                response = await client.get(url, headers=headers, follow_redirects=True)
                print(f"Status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()
                    with open(f"raw_{subreddit}.json", "w") as f:
                        json.dump(data, f, indent=2)
                        
                    children = data.get("data", {}).get("children", [])
                    print(f"Saved {subreddit} JSON to raw_{subreddit}.json (Found {len(children)} posts)")
                else:
                    print(f"Response text: {response.text[:200]}")
            except Exception as e:
                print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(fetch_raw_json())
