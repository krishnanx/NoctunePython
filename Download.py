import asyncio
import websockets
import os
import tempfile
import json
import base64
import re
EXPRESS_WS_URL = "ws://192.168.1.43:80/download-progress"

async def download_youtube_audio(urls: list[str], client_id: str):
    print(3)
    """Download multiple YouTube audios and stream progress + files to Express via WebSocket."""
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
                    "value":{"index": index,
                    "url": url,},
                    "clientId": client_id
                }))

                audio_filename_template = os.path.join(tmp_dir, f"%(title)s_{index}.%(ext)s")
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

                    # Try to extract % from progress line
                    match = re.search(r"\[download\]\s+(\d{1,3}\.\d)%", decoded_line)
                    if match:
                        percent = match.group(1)  # e.g., "42.3"
                        await ws.send(json.dumps({
                            "type": "progress",
                            "value": {
                                "index": index,
                                "percent": percent
                            },
                            "clientId": client_id
                        }))

                # Find and send the downloaded .mp3 file
                for file in os.listdir(tmp_dir):
                    if file.endswith(".mp3") and f"_{index}." in file:
                        full_path = os.path.join(tmp_dir, file)

                        with open(full_path, "rb") as f:
                            file_data = f.read()
                            encoded = base64.b64encode(file_data).decode("utf-8")

                        await ws.send(json.dumps({
                            "type": "file",
                            "value":{"index": index,
                            "filename": file,
                            "data": encoded,},
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
