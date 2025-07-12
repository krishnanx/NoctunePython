import json
import asyncio
from Waveform import get_direct_audio_url,extract_waveform_array

REDIS_KEY_PREFIX = "yt:waveform:"

async def generate_waveform_cached(yt_url, redis_client):
    cache_key = REDIS_KEY_PREFIX + yt_url

    # 1. Check cache
    cached = await redis_client.get(cache_key)
    if cached:
        print("📦 Loaded waveform from cache")
        return json.loads(cached)

    # 2. If not in cache, generate it
    def task():
        audio_url = get_direct_audio_url(yt_url)
        return extract_waveform_array(audio_url)

    waveform = await asyncio.get_event_loop().run_in_executor(None, task)

    # 3. Save to Redis (optional: set TTL)
    await redis_client.set(cache_key, json.dumps(waveform))
    print("✅ Cached waveform in Redis")

    return waveform
