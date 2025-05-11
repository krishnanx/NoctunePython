import subprocess
import json

def get_spotify_metadata(playlist_url: str):
    try:
        result = subprocess.run(
            [
                'spotdl',
                '--dry-run',
                '--output-format', 'json',
                playlist_url
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip())

        return json.loads(result.stdout)

    except subprocess.TimeoutExpired:
        raise RuntimeError("spotdl timed out.")
    except json.JSONDecodeError:
        raise RuntimeError("Invalid JSON output from spotdl.")
    except Exception as e:
        raise RuntimeError(str(e))
