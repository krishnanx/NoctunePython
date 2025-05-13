import subprocess
import json
import shutil
import tempfile
import os

def get_spotify_metadata(playlist_url: str):
    print(1)
    if shutil.which("spotdl") is None:
        raise RuntimeError("spotdl is not installed or not found in PATH.")

    # Step 1: Save track URLs from playlist
    with tempfile.NamedTemporaryFile(delete=False, suffix=".spotdl") as tmp_file:
        save_file_path = tmp_file.name

    try:
        save_result = subprocess.run(
            ['spotdl', 'save', playlist_url,"--save-file","temp.spotdl"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )
        # Optional: Print outputs for debugging
        print("[INFO] spotdl save stdout:")
        # ✅ Extract only serializable fields
        with open('temp.spotdl','r') as file:
            content = file.read()
            print(content)
            data_dict = json.loads(content)
            print(data_dict)
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
        return "hi"


    finally:
        file.close()
