import yt_dlp as youtube_dl
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import subprocess
import tempfile
import os
import uuid
import unicodedata
app = FastAPI()


def sanitize_header_value(value: str):
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")

# STEP 1: Extract video info and return duration + direct URL
def get_audio_info(url: str):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': False,
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "duration": info.get("duration"),  # in seconds
            "title": info.get("title"),
            "direct_url": info["url"],
            "thumbnail": info.get("thumbnail"),
            "uploader": info.get("uploader")
        }

# STEP 2: Stream ffmpeg output in chunks
def stream_ffmpeg_audio(input_url: str):
    # Spawn ffmpeg to convert audio from the input URL
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
    process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    def generate():
        try:
            while True:
                chunk = process.stdout.read(1024 * 32)  # 32 KB chunks
                if not chunk:
                    break
                yield chunk
        finally:
            process.stdout.close()
            process.kill()

    return generate()
@app.post("/yt/meta")
async def get_metadata(request: Request):
    try:
        body = await request.json()
        url = body["data"]
        info = await asyncio.to_thread(get_audio_info, url)
        return info
    except Exception as e:
        print("❌ Metadata fetch error:", e)
        raise HTTPException(status_code=500, detail=f"Metadata error: {e}")
@app.post("/yt")
async def stream_audio(request: Request):
    try:
        body = await request.json()
        url = body["data"]
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON. Expected {'data': '<youtube_url>'}")

    try:
        info = await asyncio.to_thread(get_audio_info, url)
    except Exception as e:
        print("❌ yt_dlp error:", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch metadata: {e}")

    try:
        generator = stream_ffmpeg_audio(info["direct_url"])
    except Exception as e:
        print("❌ ffmpeg error:", e)
        raise HTTPException(status_code=500, detail=f"Failed to start ffmpeg stream: {e}")

    headers = {
    "X-Audio-Duration": str(info["duration"]),
    "X-Audio-Title": sanitize_header_value(info["title"])
}


    return StreamingResponse(generator, media_type="audio/mpeg", headers=headers)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000, reload=False)