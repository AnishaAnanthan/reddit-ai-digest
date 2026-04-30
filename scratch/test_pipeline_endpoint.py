import httpx
import asyncio
import json

async def main():
    print("Testing /run-ranking-pipeline endpoint...")
    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post("http://127.0.0.1:8000/run-ranking-pipeline")
        if response.status_code == 200:
            print("SUCCESS!")
            data = response.json()
            print(json.dumps(data, indent=2))
        else:
            print(f"FAILED: {response.status_code}")
            print(response.text)

if __name__ == "__main__":
    asyncio.run(main())
