import httpx
import asyncio
import json

async def test_endpoints():
    base_url = "http://127.0.0.1:8000"
    endpoints = [
        ("GET", "/reddit-raw-json"),
        ("GET", "/raw-posts"),
        ("GET", "/filtered-posts"),
        ("POST", "/run-stage1"),
        # ("POST", "/run-ranking-pipeline"), # This might take too long and try to send email
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        for method, endpoint in endpoints:
            print(f"\nTesting {method} {endpoint}...")
            try:
                if method == "GET":
                    response = await client.get(f"{base_url}{endpoint}")
                else:
                    response = await client.post(f"{base_url}{endpoint}")
                
                print(f"Status: {response.status_code}")
                try:
                    data = response.json()
                    print(f"Status in JSON: {data.get('status')}")
                    if 'count' in data:
                        print(f"Count: {data['count']}")
                    # Print first 200 chars of data
                    print(f"Data snippet: {str(data)[:200]}...")
                except:
                    print(f"Response text snippet: {response.text[:200]}...")
            except Exception as e:
                print(f"Error testing {endpoint}: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
