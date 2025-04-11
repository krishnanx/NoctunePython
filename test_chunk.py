import aiohttp
import asyncio
import tempfile
import pygame
import os

URL = "http://localhost:7000/yt"
YOUTUBE_LINK = "https://www.youtube.com/watch?v=kXYiU_JCYtU"

async def fetch_and_play():
    payload = {"data": YOUTUBE_LINK}

    print("🎧 Requesting stream from server...")
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, json=payload) as resp:
            if resp.status != 200:
                print("❌ Request failed:", await resp.text())
                return

            duration = resp.headers.get("X-Audio-Duration", "?")
            title = resp.headers.get("X-Audio-Title", "Unknown")
            print(f"🎶 Streaming: '{title}' (Duration: {duration}s)")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmpfile:
                filename = tmpfile.name
                chunk_count = 0
                started = False

                while True:
                    chunk = await resp.content.read(4096)
                    if not chunk:
                        break

                    tmpfile.write(chunk)
                    chunk_count += 1

                    if not started and tmpfile.tell() > 100_000:
                        print("🔊 Starting playback...")
                        tmpfile.flush()
                        pygame.mixer.init()
                        pygame.mixer.music.load(filename)
                        pygame.mixer.music.play()
                        started = True

                print("✅ Finished receiving stream. Total chunks:", chunk_count)

    # Wait for playback to complete
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.5)

    print("✅ Playback complete.")
    os.remove(filename)

if __name__ == "__main__":
    asyncio.run(fetch_and_play())
