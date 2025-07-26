import asyncio
import websockets
import os
import tempfile
import json
import base64
import re
import requests
import traceback

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC

#EXPRESS_WS_URL = Constants.expoConfig.extra.SERVER.replace("http", "ws")/download-progress;
EXPRESS_WS_URL = "ws://127.0.0.1:80/download-progress"

def add_metadata_to_mp3(mp3_path, title, artist=None, album="YouTube Downloads", image_url=None):
    
    try:
        # Check if file exists
        if not os.path.exists(mp3_path):
            print(f"[METADATA ERROR] File does not exist: {mp3_path}")
            return False
            
        # Load the MP3 file
        audio = MP3(mp3_path, ID3=ID3)
        
        # Add tags if they don't exist
        if audio.tags is None:
            print("[METADATA] No existing tags found, adding new tags")
            audio.add_tags()
        else:
            print("[METADATA] Existing tags found, updating")

        # Clear existing tags to avoid conflicts
        audio.tags.clear()

        # Add basic metadata
        if title:
            audio.tags.add(TIT2(encoding=3, text=title))
            print(f"[METADATA] Added title: {title}")
            
        if artist:
            audio.tags.add(TPE1(encoding=3, text=artist))
            print(f"[METADATA] Added artist: {artist}")
            
        if album:
            audio.tags.add(TALB(encoding=3, text=album))
            print(f"[METADATA] Added album: {album}")

        # Add cover art if URL provided
        if image_url:
            try:
                print(f"[METADATA] Downloading cover art from: {image_url}")
                
                # Download image with headers to avoid blocking
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                img_response = requests.get(image_url, headers=headers, timeout=10)
                img_response.raise_for_status()
                
                img_data = img_response.content
                print(f"[METADATA] Downloaded {len(img_data)} bytes of image data")
                
                # Determine MIME type from content or URL
                mime_type = "image/jpeg"
                if image_url.lower().endswith('.png'):
                    mime_type = "image/png"
                elif image_url.lower().endswith('.webp'):
                    mime_type = "image/webp"
                
                audio.tags.add(APIC(
                    encoding=3,
                    mime=mime_type,
                    type=3,  # Cover (front)
                    desc="Cover",
                    data=img_data
                ))
                print(f"[METADATA] Added cover art ({mime_type})")
                
            except requests.exceptions.RequestException as e:
                print(f"[METADATA WARNING] Failed to download cover art: {e}")
            except Exception as e:
                print(f"[METADATA WARNING] Failed to add cover art: {e}")

        # Save the tags
        audio.save()
        print(f"[METADATA] Successfully saved metadata to: {mp3_path}")
        
    except Exception as e:
        print(f"[METADATA ERROR] Failed to add metadata: {e}")
        print(f"[METADATA ERROR] Traceback: {traceback.format_exc()}")
        return False

async def download_youtube_audio(items: list[dict], client_id: str):
    print(f"[DEBUG] Starting download for {len(items)} items")
    print(f"[DEBUG] Client ID: {client_id}")
    print(f"[DEBUG] WebSocket URL: {EXPRESS_WS_URL}")
    
    tmp_dir = tempfile.mkdtemp()
    print(f"[DEBUG] Temporary directory: {tmp_dir}")
    
    result = {
        "status": "success",
        "files": [],
        "error": None
    }

    try:
        print("[DEBUG] Attempting to connect to WebSocket...")
        
        # Add connection timeout and better error handling
        async with websockets.connect(
            EXPRESS_WS_URL, 
            max_size=2**25,
            ping_timeout=20,
            ping_interval=30
        ) as ws:
            print("[DEBUG] WebSocket connection established successfully!")
            
            print("[DEBUG] Received URLs (with metadata):")
            for i, item in enumerate(items):
                print(f"  [{i}] Title: {item.get('title')}, Artist: {item.get('uploader') or item.get('artist')}, Image: {item.get('image')}, URL: {item.get('url')}")

            for index, item in enumerate(items):
                try:
                    url = item["url"]
                    title = item.get("title", f"Track {index}")
                    artist = item.get("uploader") or item.get("artist") or "Unknown Artist"
                    thumbnail = item.get("image")

                    print(f"[DEBUG] Processing item {index}: {title} by {artist}")

                    await ws.send(json.dumps({
                        "type": "start",
                        "value": {"index": index, "url": url},
                        "clientId": client_id
                    }))

                    # Create a safer filename template
                    safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)  # Replace invalid chars
                    audio_filename_template = os.path.join(tmp_dir, f"{safe_title}_{index}.%(ext)s")
                    print(f"[DEBUG] Output template: {audio_filename_template}")

                    ytdlp_cmd = [
                        "yt-dlp",
                        "-f", "bestaudio",
                        "-o", audio_filename_template,
                        "--no-playlist",
                        "--extract-audio",
                        "--audio-format", "mp3",
                        "--newline",
                        "--no-warnings",  # Reduce noise
                        url
                    ]

                    print(f"[DEBUG] Running command: {' '.join(ytdlp_cmd)}")

                    process = await asyncio.create_subprocess_exec(
                        *ytdlp_cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.STDOUT
                    )

                    # Process yt-dlp output
                    while True:
                        line = await process.stdout.readline()
                        if not line:
                            break
                        decoded_line = line.decode().strip()
                        print(f"[yt-dlp:{index}]:", decoded_line)

                        # Extract progress
                        match = re.search(r"\[download\]\s+(\d{1,3}\.\d)%", decoded_line)
                        if match:
                            percent = match.group(1)
                            print(percent)
                            await ws.send(json.dumps({
                                "type": "progress",
                                "value": {"index": index, "percent": percent},
                                "clientId": client_id
                            }))

                    # Wait for process to complete
                    await process.wait()
                    print(f"[DEBUG] yt-dlp process completed with return code: {process.returncode}")

                    # Find the downloaded file
                    downloaded_file = None
                    print(f"[DEBUG] Looking for downloaded files in: {tmp_dir}")
                    
                    for file in os.listdir(tmp_dir):
                        print(f"[DEBUG] Found file: {file}")
                        if file.endswith(".mp3") and f"_{index}." in file:
                            downloaded_file = file
                            break

                    if not downloaded_file:
                        print(f"[ERROR] No MP3 file found for index {index}")
                        continue

                    full_path = os.path.join(tmp_dir, downloaded_file)
                    print(f"[DEBUG] Processing downloaded file: {full_path}")
                    print(f"[DEBUG] File size: {os.path.getsize(full_path)} bytes")

                    # Add metadata BEFORE sending file
                    print(f"[DEBUG] Adding metadata to: {full_path}")
                    print(f"[DEBUG] Metadata - Title: {title}, Artist: {artist}, Thumbnail: {thumbnail}")
                    
                    metadata_success = add_metadata_to_mp3(full_path, title, artist, "YouTube Downloads", thumbnail)
                    
                    if not metadata_success:
                        print(f"[WARNING] Metadata addition failed for {full_path}")

                    # Read and encode file
                    try:
                        with open(full_path, "rb") as f:
                            file_data = f.read()
                            encoded = base64.b64encode(file_data).decode("utf-8")
                        
                        print(f"[DEBUG] File encoded, size: {len(encoded)} characters")

                        # Send file via WebSocket
                        await ws.send(json.dumps({
                            "type": "file",
                            "value": {
                                "index": index,
                                "filename": downloaded_file,
                                "data": encoded
                            },
                            "clientId": client_id
                        }))

                        result["files"].append(full_path)
                        print(f"[DEBUG] Successfully processed item {index}")
                        
                    except Exception as e:
                        print(f"[ERROR] Failed to read/encode file {full_path}: {e}")
                        print(f"[ERROR] Traceback: {traceback.format_exc()}")

                except Exception as e:
                    print(f"[ERROR] Error processing item {index}: {e}")
                    print(f"[ERROR] Traceback: {traceback.format_exc()}")
                    continue

        print("[DEBUG] All items processed successfully")
        return result

    except websockets.exceptions.InvalidHandshake as e:
        error_msg = f"WebSocket handshake failed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        result["status"] = "error"
        result["error"] = error_msg
        return result
    except websockets.exceptions.ConnectionClosedError as e:
        error_msg = f"WebSocket connection closed: {str(e)}"
        print(f"[ERROR] {error_msg}")
        result["status"] = "error"
        result["error"] = error_msg
        return result
    except asyncio.TimeoutError as e:
        error_msg = "WebSocket connection timed out - check if the WebSocket server is running"
        print(f"[ERROR] {error_msg}")
        result["status"] = "error"
        result["error"] = error_msg
        return result
    except ConnectionRefusedError as e:
        error_msg = f"Connection refused - WebSocket server may not be running at {EXPRESS_WS_URL}"
        print(f"[ERROR] {error_msg}")
        result["status"] = "error"
        result["error"] = error_msg
        return result
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        print(f"[ERROR] Full traceback: {traceback.format_exc()}")
        result["status"] = "error"
        result["error"] = error_msg
        return result