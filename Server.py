import yt_dlp as youtube_dl  # Keep for ffmpeg reconnect options
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import subprocess
import tempfile
import os
import uuid
import unicodedata
import time
import json

app = FastAPI()

def sanitize_header_value(value: str):
    """Make header values safe ASCII."""
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")

# STEP 1: Extract metadata quickly using yt-dlp subprocess
def get_audio_info(url: str):
    """Fetch audio info using yt-dlp subprocess (faster)."""
    try:
        result = subprocess.run(
            [
                "yt-dlp", "--quiet", "--no-warnings",
                "--no-playlist", "--skip-download",
                "--extractor-args", "youtube:player_client=android",
               "--print", "url", url
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15
        )

        if result.returncode != 0:
            raise ValueError(f"yt-dlp error: {result.stderr.decode().strip()}")

        direct_url = result.stdout.decode().strip()

        if not direct_url.startswith("http"):
            raise ValueError("Direct URL extraction failed.")

        return {"direct_url": direct_url}

    except subprocess.TimeoutExpired:
        raise ValueError("yt-dlp subprocess timed out.")
    except Exception as e:
        raise ValueError(f"Metadata fetch error: {e}")

# STEP 2: Stream audio via ffmpeg
async def stream_ffmpeg_audio(input_url: str):
    """Launch ffmpeg to convert and stream audio."""
    ffmpeg_cmd = [
        "ffmpeg",
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "2",
        "-i", input_url,
        "-vn",
        "-acodec", "libmp3lame",
        "-f", "mp3",
        "-b:a", "192k",
        "-fflags", "+genpts",
        "-hide_banner",
        "-loglevel", "error",
        "pipe:1"
    ]
    
    process = await asyncio.create_subprocess_exec(*ffmpeg_cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)

    def generate():
        try:
            while True:
                chunk = process.stdout.read(1024 * 8)  # 8 KB chunks
                if not chunk:
                    break
                yield chunk
        finally:
            process.stdout.close()
            process.kill()

    return generate()

# === ROUTES ===

@app.post("/yt/meta")
async def get_metadata(request: Request):
    """Return metadata of the YouTube audio."""
    start_time = time.time()

    try:
        body = await request.json()
        url = body["data"]
        info = await asyncio.to_thread(get_audio_info, url)

        end_time = time.time()
        duration = end_time - start_time
        print(f"⏱️ Metadata fetch took {duration:.2f} seconds.")

        return info

    except Exception as e:
        print("Metadata fetch error:", e)
        raise HTTPException(status_code=500, detail=f"Metadata error: {e}")

@app.post("/yt")
async def stream_audio(request: Request):
    """Stream YouTube audio converted to MP3."""
    start_time = time.time()
    try:
        body = await request.json()
        url = body["data"]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON. Expected {'data': '<youtube_url>'}")

    try:
        info = await asyncio.to_thread(get_audio_info, url)
    except Exception as e:
        print("yt-dlp error:", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch metadata: {e}")

    try:
        end_time = time.time()
        duration = end_time - start_time
        print(f"⏱️ Metadata fetch took {duration:.2f} seconds.")
        generator = stream_ffmpeg_audio(info["direct_url"])
    except Exception as e:
        print("ffmpeg error:", e)
        raise HTTPException(status_code=500, detail=f"Failed to start ffmpeg stream: {e}")

    # headers = {
    #     "X-Audio-Duration": str(info["duration"]),
    #     "X-Audio-Title": sanitize_header_value(info["title"])
    # }

    return StreamingResponse(generator, media_type="audio/mpeg")
@app.get("/ping")
def warmConnection():
    print("Express says: ping")
    return "pong"
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Server:app", host="0.0.0.0", port=7000, reload=True)
