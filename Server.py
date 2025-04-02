from fastapi import FastAPI, Query
from pytube import YouTube
from pydantic import BaseModel
import os
import uvicorn
app = FastAPI()
if __name__ == "__main__":
    uvicorn.run("Server:app", host="0.0.0.0", port=8000, reload=True)
class DownloadRequest(BaseModel):
    data: str  # Ensure the request contains a "data" field
@app.post("/yt")
async def download_audio(request: DownloadRequest):

    try:
        print(request.data)
        data = request.data
         # Get JSON data
        url = data.get("url")  # Extract 'url' from JSON
        destination = data.get("destination", ".")
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
