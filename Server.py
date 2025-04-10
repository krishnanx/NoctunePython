import yt_dlp as youtube_dl
from fastapi import FastAPI, Response, HTTPException, Request
import os
import uuid
import asyncio
from concurrent.futures import ProcessPoolExecutor

app = FastAPI()
executor = ProcessPoolExecutor()

def download_and_convert(url: str, filename: str) -> bytes:
    """Download YouTube audio and return MP3 content"""
    try:
        base_output = f"/tmp/{filename}"  # no extension
        final_output_path = f"{base_output}.mp3"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': base_output,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
            'quiet': True,
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(final_output_path) or os.stat(final_output_path).st_size == 0:
            raise ValueError("Downloaded file is empty!")

        with open(final_output_path, "rb") as f:
            mp3_data = f.read()

        os.remove(final_output_path)  # Clean up
        return mp3_data

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/yt")
async def download_audio(request: Request):
    try:
        body = await request.json()
        url = body["data"]
    except:
        raise HTTPException(status_code=400, detail="Invalid JSON. Expected {'data': '<youtube_url>'}")

    filename = str(uuid.uuid4())

    # Offload the blocking task
    loop = asyncio.get_event_loop()
    mp3_data = await loop.run_in_executor(executor, download_and_convert, url, filename)

    return Response(content=mp3_data, media_type="audio/mpeg")
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000, reload=False)