# NoctunePython - FastAPI Server for Noctune

NoctunePython is the FastAPI backend for **Noctune**, a free and open-source music streaming app. This backend acts as a bridge between third-party services and the Noctune frontend, providing core functionality like playlist migration, streaming, and downloading of music.

---

## 🔄 Noctune Sync - Migrating Spotify Playlists

Noctune Sync enables users to migrate their existing Spotify playlists to the Noctune platform.

### How it works:

1. The frontend collects the link for Spotify playlist.
2. The backend receives this link via a POST request.
3. Each music from the playlist is extracted.
4. Each track is converted into a YouTube search query (e.g., "Blinding Lights The Weeknd").
5. `yt_dlp` is used to search and extract the best audio source from YouTube.
6. Metadata such as title, thumbnail, duration, and URL are fetched.
7. The backend responds with a list of enriched tracks ready for import into the Noctune library.


## 🎧 Music Streaming

Streams music in real-time from YouTube directly to the Noctune frontend.

### How it works:

* Accepts a YouTube URL as a query parameter.
* Uses `yt_dlp` to extract the direct audio stream.
* Streams audio through FFmpeg, which pipes and converts it to a supported format (e.g., `.m4a`).
* The client receives a seamless audio stream for playback.

### Endpoint:

```
GET /stream?url=<YouTubeURL>
```

Returns:

* Audio stream (`audio/mpeg` or `audio/mp4`)

---

## 💾 Music Downloading

Allows users to download music from YouTube for offline listening.

### How it works:

* Accepts a POST request with the YouTube URL and desired filename.
* Downloads audio using `yt_dlp` and stores it in a structured directory.
* The file is named and cached to prevent repeated downloads.
* Returns the path of the downloaded file.

### Endpoint:

```
POST /download
```

Payload:

```json
{
  "url": "https://youtube.com/watch?v=...",
  "title": "Blinding Lights"
}
```

Response:

```json
{
  "status": "downloaded",
  "path": "/downloads/blinding_lights.m4a"
}
```

---

## 🧠 Future Plans - Music Recommendations

The backend will soon support intelligent music recommendations powered by audio embeddings and user behavior analysis.

* Embedding models (e.g., Musicnn, OpenL3)
* Track similarity via vector distance
* Feedback signals (skip, boost) to refine recommendations

### Planned Endpoint:

```
POST /recommend
```

---

## 📂 Repository Structure (Simplified)

```
NoctunePython/
├── app/
│   ├── main.py              # FastAPI entrypoint
│   ├── routes/
│   │   ├── stream.py        # Audio streaming endpoint
│   │   ├── download.py      # Downloading logic
│   │   └── sync.py          # Noctune Sync handler
│   └── services/            # yt_dlp, ffmpeg, utils
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

* **FastAPI** for building async APIs
* **yt\_dlp** for YouTube scraping
* **FFmpeg** for stream conversion and audio handling


---

## 👨‍💻 Author

Developed and maintained by [Krishnan](https://github.com/krishnanx)

Feel free to contribute, raise issues, or suggest enhancements!

