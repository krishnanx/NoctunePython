from fastapi import FastAPI
from pydantic import BaseModel
from pydub import AudioSegment
import os
import uvicorn
import yt_dlp as youtube_dl

app = FastAPI()

class DownloadRequest(BaseModel):
    data: str  # Ensure the request contains a "data" field

@app.post("/yt")
async def download_audio(request: DownloadRequest):
    try:
        url = request.data
        destination = "Music"
        os.makedirs(destination, exist_ok=True)

        # Download video using yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': os.path.join(destination, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return {"message": "Download and conversion complete."}

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
