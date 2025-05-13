import asyncio
import websockets
import os
import tempfile
import json
import base64
import re
import requests

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC

EXPRESS_WS_URL = "ws://192.168.1.44:80/download-progress"

def add_metadata_to_mp3(mp3_path, title, artist=None, album="YouTube Downloads", image_url=None):
    audio = MP3(mp3_path, ID3=ID3)
    if audio.tags is None:
        audio.add_tags()

    audio.tags.add(TIT2(encoding=3, text=title))  # Title
    if artist:
        audio.tags.add(TPE1(encoding=3, text=artist))  # Artist
    audio.tags.add(TALB(encoding=3, text=album))  # Album

    if image_url:
        try:
            img_data = requests.get(image_url).content
            audio.tags.add(APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="Cover",
                data=img_data
            ))
        except Exception as e:
            print("Failed to download or add image:", e)

    audio.save()

async def download_youtube_audio(urls: list[str], client_id: str):
    print(3)
    tmp_dir = tempfile.mkdtemp()
    result = {
        "status": "success",
        "files": [],
        "error": None
    }

    try:
        async with websockets.connect(EXPRESS_WS_URL, max_size=2**25) as ws:
            print(4)
            for index, url in enumerate(urls):
                await ws.send(json.dumps({
                    "type": "start",
                    "value": {"index": index, "url": url},
                    "clientId": client_id
                }))

                audio_filename_template = os.path.join(tmp_dir, f"%(title)s_{index}.%(ext)s")
                # Get metadata info first
                ytdlp_info_cmd = [
                    "yt-dlp", "-j", "--no-playlist", url
                ]
                proc = await asyncio.create_subprocess_exec(
                    *ytdlp_info_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                stdout, stderr = await proc.communicate()
                metadata = json.loads(stdout.decode())

                title = metadata.get("title", f"Track {index}")
                artist = metadata.get("uploader")
                thumbnail = metadata.get("thumbnail")

                ytdlp_cmd = [
                    "yt-dlp",
                    "-f", "bestaudio",
                    "-o", audio_filename_template,
                    "--no-playlist",
                    "--extract-audio",
                    "--audio-format", "mp3",
                    "--newline",
                    url
                ]

                process = await asyncio.create_subprocess_exec(
                    *ytdlp_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.STDOUT
                )

                while True:
                    line = await process.stdout.readline()
                    if not line:
                        break
                    decoded_line = line.decode().strip()
                    print(f"[yt-dlp:{index}]:", decoded_line)

                    match = re.search(r"\[download\]\s+(\d{1,3}\.\d)%", decoded_line)
                    if match:
                        percent = match.group(1)
                        await ws.send(json.dumps({
                            "type": "progress",
                            "value": {"index": index, "percent": percent},
                            "clientId": client_id
                        }))

                for file in os.listdir(tmp_dir):
                    if file.endswith(".mp3") and f"_{index}." in file:
                        full_path = os.path.join(tmp_dir, file)

                        # # Add metadata to MP3 before base64 encoding
                        add_metadata_to_mp3(full_path, title, artist, "YouTube Downloads", thumbnail)

                        with open(full_path, "rb") as f:
                            file_data = f.read()
                            encoded = base64.b64encode(file_data).decode("utf-8")

                        await ws.send(json.dumps({
                            "type": "file",
                            "value": {
                                "index": index,
                                "filename": file,
                                "data": encoded
                            },
                            "clientId": client_id
                        }))

                        result["files"].append(full_path)
                        break

        return result

    except Exception as e:
        print("Download error:", e)
        result["status"] = "error"
        result["error"] = str(e)
        return result
