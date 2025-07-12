
import subprocess
import numpy as np
import tempfile
import os
from scipy.signal import resample
import yt_dlp
from fastapi import HTTPException


def get_direct_audio_url(youtube_url: str) -> str:
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio/best/18',  # 18 = 360p mp4 with audio
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            info = ydl.extract_info(youtube_url, download=False)
            return info['url']
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"yt-dlp failed: {str(e)}")

def extract_waveform_array(audio_url_or_path: str, num_samples: int = 150) -> list:
    with tempfile.NamedTemporaryFile(suffix=".raw", delete=False) as temp_pcm:
        temp_pcm_path = temp_pcm.name

    try:
        # ffmpeg command to extract raw PCM mono audio at 8000 Hz
        cmd = [
            "ffmpeg",
            "-y",
            "-i", audio_url_or_path,
            "-f", "s16le",  # 16-bit signed little endian
            "-acodec", "pcm_s16le",
            "-ac", "1",     # mono
            "-ar", "8000",  # sample rate
            "-loglevel", "quiet",
            temp_pcm_path
        ]

        subprocess.run(cmd, check=True)

        # Read the raw data
        raw_audio = np.fromfile(temp_pcm_path, dtype=np.int16)

        if raw_audio.size == 0:
            return []

        # Normalize
        raw_audio = np.abs(raw_audio)

        # Resample to num_samples points
        waveform = resample(raw_audio, num_samples)
        normalized = np.clip((waveform / np.max(waveform)), 0, 1)

        return (normalized * 100).astype(int).tolist()

    finally:
        os.remove(temp_pcm_path)

