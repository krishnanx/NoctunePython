import yt_dlp as youtube_dl
from fastapi import FastAPI, Response, HTTPException
import os

app = FastAPI()

def download_and_convert(url: str):
    """Download YouTube audio and return MP3 content"""
    try:
        output_path = "output_audio"  # yt-dlp appends ".mp3" after conversion
        final_output_path = f"{output_path}.mp3"  # Ensure we check the correct file

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,  # yt-dlp appends .mp3 later
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'noplaylist': True,
            'quiet': False,  # Show logs for debugging
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Ensure file exists and is not empty
        if not os.path.exists(final_output_path) or os.stat(final_output_path).st_size == 0:
            raise ValueError("Downloaded file is empty!")

        with open(final_output_path, "rb") as f:
            mp3_data = f.read()

        os.remove(final_output_path)  # Clean up after sending the file

        return mp3_data

    except Exception as e:
        print("Error:", e)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/yt")
def download_audio(request: dict):
    url = request["data"]
    print(f"Downloading: {url}")

    mp3_data = download_and_convert(url)

    print(f"Returning MP3 file for: {url}")
    return Response(content=mp3_data, media_type="audio/mpeg")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7000, reload=False)
