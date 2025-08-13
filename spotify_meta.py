import subprocess
import json
import shutil
import tempfile
import os
import asyncio
import websockets
EXPRESS_WS_URL = "ws://127.0.0.1:80/download-progress"
async def get_spotify_metadata(playlist_url: str,user):
    print(1)
    if shutil.which("spotdl") is None:
        raise RuntimeError("spotdl is not installed or not found in PATH.")

    #Step 1: Save track URLs from playlist
    with tempfile.NamedTemporaryFile(delete=False, suffix=".spotdl") as tmp_file:
        save_file_path = tmp_file.name
    # with open('play.spotdl','w') as file:
    #     pass
    try:
        async with websockets.connect(
            EXPRESS_WS_URL, 
            max_size=2**25,
            ping_timeout=20,
            ping_interval=30
        ) as ws:
            with open('play.spotdl', 'w') as file:
                file.truncate(0)
            save_result = subprocess.run(
                ['spotdl', 'save', playlist_url,'--playlist-retain-track-cover', '--fetch-albums', '--save-file', 'play.spotdl'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60
            )

            print(save_result.stdout)
            # Optional: Print outputs for debugging
            print("[INFO] spotdl save stdout:")
            # ✅ Extract only serializable fields
            with open('play.spotdl','r') as file:
                content = file.read()
                # print(content)
                data_dict = json.loads(content)
                
            print(f"\n🎵 Total Songs: {len(data_dict)}")
            for idx, song in enumerate(data_dict, 1):
                song_title = song.get('name')
                song_artist = song.get('artist')
                song_album = song.get('album')
                song_cover_url = song.get('coverUrl')
                id = await asyncio.to_thread(get_youtube_url, song_title, song_artist)
                song["song_id"] = id
                song['url'] = f"https://www.youtube.com/watch?v={id}"
                print(f"\n--- Song {idx} ---")
                print(f"Title     : {song_title}")
                print(f"Artist    : {song_artist}")
                print(f"Album     : {song_album}")
                print(f"YouTube URL: {song.get('url')}")
                print(f"Cover URL : {song_cover_url}")
            
            print(data_dict)
            print("user",user)
            await ws.send(json.dumps({
                "type": "migrate",
                "value": data_dict,
                "clientId": user
            }))

            return data_dict
        # Check for errors
        # if save_result.returncode != 0:
        #     raise RuntimeError(f"spotdl save failed: {save_result.stderr.strip()}")
        # with open(save_file_path, 'r') as f:
        #     track_urls = [line.strip() for line in f if line.strip()]

        # if not track_urls:
        #     raise RuntimeError("No tracks found in playlist.")

                # Step 2: Run 'spotdl meta' on each track
        # metadata = []
        # for track_url in track_urls:
        #     meta_result = subprocess.run(
        #         ['spotdl', 'meta', track_url],
        #         stdout=subprocess.PIPE,
        #         stderr=subprocess.PIPE,
        #         text=True,
        #         timeout=30
        #     )

        #     if meta_result.returncode != 0:
        #         print(f"[ERROR] Failed on track: {track_url}")
        #         print(f"[STDERR] {meta_result.stderr}")
        #         raise RuntimeError(meta_result.stderr.strip())

        #     raw_output = meta_result.stdout.strip()
        #     print(f"[DEBUG] spotdl meta output for {track_url}:\n{raw_output}\n")

        #     try:
        #         parsed = json.loads(raw_output)
        #         metadata.append(parsed)
        #     except json.JSONDecodeError:
        #         raise RuntimeError(f"Invalid JSON from spotdl for track {track_url}:\n{raw_output}")

        # return metadata
    finally:
        print("Done")
def get_youtube_url(song_name, artist_name):
        # Construct the search query
        search_query = f"ytsearch:{song_name} {artist_name}"
        
        # Use yt-dlp to search YouTube and get the URL
        result = subprocess.run(
            ['yt-dlp', '--get-id', search_query],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Error: {result.stderr}"