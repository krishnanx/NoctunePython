import yt_dlp as youtube_dl  # Keep for ffmpeg reconnect options
from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.responses import StreamingResponse, JSONResponse
import asyncio
import subprocess
import tempfile
import os
import uuid
import unicodedata
import time
import json
import yt_dlp
from Download import download_youtube_audio 
from spotify_meta import get_spotify_metadata
from Redis import CreateEmptyPlaylist,get_all_playlists_as_array,storeData,EditPlaylist,persistMusics,getpersistMusics
import redis.asyncio as redis
from dotenv import load_dotenv
import asyncpg
from yt_dlp import YoutubeDL
from Waveform import extract_waveform_array,get_direct_audio_url
import numpy as np
from redis_cache import generate_waveform_cached
 


app = FastAPI()
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


@app.on_event("startup")
async def startup():
    global redis_client
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    global db_pool
    # DATABASE_URL = os.getenv("DATABASE_URL")
    try:
        await redis_client.ping()
        # db_pool = await asyncpg.create_pool(DATABASE_URL)
        print("🔗 Connected to Redis")
    except Exception as e:
        print(f"Redis connection failed: {e}")

@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()
        await db_pool.close()
        print("🔌 Redis connection closed")



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
def stream_ffmpeg_audio(input_url: str):
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
    process = subprocess.Popen(
        ffmpeg_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

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
        print("url:", url)
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

@app.post("/download")
async def download(request: Request, client_id: str = Header(..., alias="client-id")):
    try:
        body = await request.json()
        data = body["data"]
        print(f"[DEBUG] Received data: {data}")
        print(f"[DEBUG] Data type: {type(data)}")
        print(f"[DEBUG] Client ID: {client_id}")
        
        # Handle both list of URLs and list of objects with metadata
        items = []
        if isinstance(data, list):
            for item in data:
                if isinstance(item, str):
                    # Simple URL string - create basic item object
                    items.append({
                        "url": item,
                        "title": f"Track_{len(items)}",
                        "uploader": "Unknown Artist",
                        "artist": None,
                        "image": None
                    })
                elif isinstance(item, dict):
                    # Already an object with metadata - ensure required fields exist
                    items.append({
                        "url": item.get("url", ""),
                        "title": item.get("title", f"Track_{len(items)}"),
                        "uploader": item.get("uploader", "Unknown Artist"),
                        "artist": item.get("artist"),
                        "image": item.get("image")
                    })
                else:
                    raise ValueError(f"Invalid item type: {type(item)}. Expected string URL or object.")
        else:
            raise ValueError("Expected 'data' to be a list of URLs or objects.")
        
        print(f"[DEBUG] Processed {len(items)} items for download")
        
    except KeyError:
        raise HTTPException(status_code=400, detail="Missing 'data' field in request body")
    except Exception as e:
        print(f"[ERROR] Request parsing error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request format: {str(e)}")

    try:
        result = await download_youtube_audio(items, client_id)
        
        if result["status"] == "error":
            raise HTTPException(status_code=500, detail=result["error"])

        return JSONResponse({
            "message": "All downloads complete",
            "files": [os.path.basename(f) for f in result["files"]],
            "status": "success"
        })
        
    except Exception as e:
        print(f"[ERROR] Download processing error: {e}")
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


    try:
        body = await request.json()
        urls = body["data"]
        print(1)
        if not isinstance(urls, list) or not all(isinstance(u, str) for u in urls):
            raise ValueError("Expected 'data' to be a list of YouTube URLs.")

    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON. Expected {'data': ['url1', 'url2', ...]}")
    print(2)
    result = await download_youtube_audio(urls,client_id)

    if result["status"] == "error":
        raise HTTPException(status_code=500, detail=result["error"])

    return JSONResponse({
        "message": "All downloads complete",
        "files": [os.path.basename(f) for f in result["files"]]
    })
@app.post("/spotify/meta")
async def fetch_spotify_metadata(request: Request):
    """Fetch metadata from a Spotify playlist using spotDL."""
    try:
        body = await request.json()
        playlist_url = body.get("data")
        if not playlist_url:
            raise HTTPException(status_code=400, detail="Missing 'data' with Spotify playlist URL")

        metadata = await asyncio.to_thread(get_spotify_metadata, playlist_url)
        print("lessgoo")
        return metadata

    except Exception as e:
        print("spotDL error:", e)
        raise HTTPException(status_code=500, detail=f"Failed to fetch metadata: {e}")
@app.post("/playlist/Emptynew")
async def add_new_playlist(request: Request):
    try:
        body = await request.json()
        playlist = body.get("data")
        user = body.get("user")
        if not playlist:
            raise HTTPException(status_code=400, detail="Missing 'data' with playlist")
        
        response = await CreateEmptyPlaylist(redis_client,playlist,user)
        if(response == "playlist exists"):
            return 0
        return 1
    except Exception as e:
        print(e)

@app.post("/playlist/editPlaylist")
async def edit_playlist(request: Request):
    try:
        body = await request.json()
        playlist = body.get("playlist")
        user = body.get("user")
        original_name = body.get("originalName")  # 👈 handle originalName from frontend

        if not playlist or not user:
            raise HTTPException(status_code=400, detail="Missing playlist or user")

        response = await EditPlaylist(redis_client, playlist, user, original_name)
        return response  # send the response directly

    except Exception as e:
        print(f"Error in edit_playlist: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# @app.post("/playlist/new")
# async def addPlaylistWithData(request: Request):
#     try:
#         body = await request.json()
#         playlist = body.get("data")
#         new_song = body.get("newsong")
#         if not playlist:
#             raise HTTPException(status_code=400, detail="Missing 'data' with playlist")
        
#         response = await CreatesandStoreData(redis_client,playlist,new_song)
#         if(response == "playlist exists"):
#             return 0
#         return 1
#     except Exception as e:
#         print(e)
@app.post("/playlist/get")
async def pullplaylists( request: Request):
    try:
        print("reached playlist pull")
        body = await request.json()
        user = body.get("user")
        print("user:",user)
        response = await get_all_playlists_as_array(redis_client,user)
        return response
    except Exception as e:
        print(e)
@app.post("/playlist/addMusic")
async def addMusic(request: Request):
    try:
        body = await request.json()
        user = body.get("user")
        playlist = body.get("data")
        playlist_name = playlist["name"]
        print("playlist name:", playlist_name)
        new_song = body.get("music")
        response = await storeData(redis_client,playlist_name,new_song,user)
        return response
    except Exception as e:
        print("adding music to playlist didnt work",e)

@app.post("/redis/searchedMusic")
async def addsearchedMusic(request:Request):
    try:
        body = await request.json()
        user = body.get("user")
        searchedMusics = body.get("data")
        
        
        response = await persistMusics(redis_client,searchedMusics,user)
        return response
    except Exception as e:
        print("adding music to playlist didnt work",e)

@app.post("/redis/getsearchedMusic")
async def getSearchedMusics(request:Request):
    try:
        body = await request.json()
        user = body.get("user")

        response = await getpersistMusics(redis_client,user)
        return response
    except Exception as e:
        print(e)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("Server:app", host="0.0.0.0", port=7000, reload=True)



# Blocking function
def get_direct_audio_url(yt_url):
    ydl_opts = {
        'quiet': True,
        'format': 'bestaudio[ext=m4a]/bestaudio/best', #[ext=webm
        'noplaylist': True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(yt_url, download=False)
        return info['url']

# Blocking function
def extract_waveform_array(audio_url):
    with tempfile.NamedTemporaryFile(suffix=".raw") as tmpfile:
        raw_path = tmpfile.name

        # ffmpeg
        cmd = [
            "ffmpeg", "-y", "-i", audio_url,
            "-t","30",
            "-f", "s16le",
            "-acodec", "pcm_s16le",
            "-ac", "1",
            "-ar", "8000",
            "-loglevel", "quiet",
            raw_path,
        ]
        subprocess.run(cmd, check=True)

        with open(raw_path, "rb") as f:
            pcm_data = np.frombuffer(f.read(), dtype=np.int16)
            abs_amplitude = np.abs(pcm_data)

            segment_size = len(abs_amplitude) // 200
            waveform = [
                int(np.mean(abs_amplitude[i:i + segment_size]) / 32767 * 100)
                for i in range(0, len(abs_amplitude), segment_size)
            ]
            return waveform[:200]

# Async wrapper to avoid blocking FastAPI
async def generate_waveform(yt_url):
    loop = asyncio.get_event_loop()

    def task():
        audio_url = get_direct_audio_url(yt_url)
        return extract_waveform_array(audio_url)

    return await loop.run_in_executor(None, task)

@app.post("/yt/waveform")
async def get_waveform(request: Request):
    start_time = time.time()
    try:
        body = await request.json()
        
        yt_url = body.get("data")
        if not yt_url:
            raise HTTPException(status_code=400, detail="Missing 'data' (YouTube URL)")

        
        waveform = await generate_waveform_cached(yt_url, redis_client)
        if not waveform:
            waveform = await generate_waveform(yt_url)
            await redis_client.set(yt_url, json.dumps(waveform))
        end_time = time.time()  # ✅ End timer
        duration = end_time - start_time
        print(f"⏱️ Waveform generation took {duration:.2f} seconds.")

        return {"waveform": waveform}

    except Exception as e:
        print("Waveform error:", e)
        raise HTTPException(status_code=500, detail=f"Waveform error: {str(e)}")

