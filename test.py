import asyncio
import aiohttp
import time

# Your FastAPI endpoint
URL = "http://localhost:7000/yt"

# List of YouTube links to test with
YT_LINKS = [
    "https://www.youtube.com/watch?v=DLzxrzFCyOs",  # Rick Astley
    "https://www.youtube.com/watch?v=3JZ_D3ELwOQ",  # Linkin Park - Numb
    "https://www.youtube.com/watch?v=kXYiU_JCYtU",  # Linkin Park - In the End
    "https://www.youtube.com/watch?v=9bZkp7q19f0",  # PSY - Gangnam Style
    "https://www.youtube.com/watch?v=l482T0yNkeo",  # Queen - Bohemian Rhapsody
]

async def fetch_audio(session, url):
    payload = {"data": url}
    start = time.time()
    try:
        async with session.post(URL, json=payload, timeout=600) as response:
            if response.status != 200:
                print(f"[{url}] ❌ Failed: HTTP {response.status}")
                return
            mp3_data = await response.read()
            duration = time.time() - start
            print(f"[{url}] ✅ Success! Got {len(mp3_data)} bytes in {duration:.2f} seconds")
    except Exception as e:
        print(f"[{url}] ❌ Error: {e}")

async def main():
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_audio(session, yt) for yt in YT_LINKS]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
