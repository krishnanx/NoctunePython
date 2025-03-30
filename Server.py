from fastapi import FastAPI, Query
from pytube import YouTube
import os

app = FastAPI()

@app.get("/download/")
def download_audio(url: str, destination: str = "."):
    try:
        yt = YouTube(url)
        audio_stream = yt.streams.filter(only_audio=True).first()
        out_file = audio_stream.download(output_path=destination)

        # Rename to MP3
        base, ext = os.path.splitext(out_file)
        new_file = base + ".mp3"
        os.rename(out_file, new_file)

        return {"message": f"{yt.title} has been downloaded as MP3", "file": new_file}

    except Exception as e:
        return {"error": str(e)}

# Run the server with:
# uvicorn filename:app --reload
