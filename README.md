<div align="center">

# 🎵 Noctune Backend

### High-performance FastAPI backend powering the Noctune music streaming ecosystem

*A scalable backend responsible for music streaming, playlist migration, downloads, waveform generation, metadata management, and real-time communication.*

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Async-green)
![Redis](https://img.shields.io/badge/Redis-Cache-red)
![FFmpeg](https://img.shields.io/badge/FFmpeg-Audio-orange)
![yt-dlp](https://img.shields.io/badge/yt--dlp-Streaming-yellow)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

</div>

---

# Overview

The **Noctune Backend** is the core service behind the Noctune music application. It provides APIs for streaming music, downloading tracks, migrating Spotify playlists, generating waveforms, retrieving lyrics, and managing user playlists.

Rather than storing copyrighted media, the backend intelligently integrates multiple services to fetch metadata, stream audio, and enrich the listening experience.

---

# Features

## 🎧 Music Streaming

- Low-latency audio streaming
- Direct YouTube audio extraction
- FFmpeg transcoding pipeline
- Automatic reconnection handling
- High-quality MP3 streaming

---

## 📥 Music Downloads

- Download songs from YouTube
- Automatic metadata embedding
- Album artwork support
- Artist and album information
- Download progress via WebSockets

---

## 🔄 Spotify Playlist Migration

Migrate Spotify playlists into Noctune in a few steps.

The backend:

- Reads Spotify playlist metadata
- Extracts song information
- Finds the best YouTube match
- Returns playable tracks
- Preserves playlist ordering

---

## 📊 Waveform Generation

Generate waveform data used by the Noctune player.

Features include:

- Audio analysis
- Cached waveform generation
- Faster repeat requests
- Optimized for mobile visualization

---

## 🎤 Lyrics Integration

Retrieve synchronized song lyrics using the Genius API.

Supports:

- Artist lookup
- Song lookup
- Clean lyric formatting

---

## 📚 Playlist Management

Backend support for:

- Playlist creation
- Playlist editing
- Playlist deletion
- Persistent storage
- Redis caching

---

## ⚡ Redis Cache

Redis is used for:

- Temporary playlist migration
- Cached waveform data
- Session storage
- Faster API responses

---

# Architecture

```text
                    Noctune Mobile App
                             │
                             │ REST API
                             ▼
                    FastAPI Backend
                             │
     ┌───────────────┬───────────────┬───────────────┐
     │               │               │               │
     ▼               ▼               ▼               ▼
 Streaming      Downloads      Playlist Sync     Lyrics
     │               │               │               │
 yt-dlp         FFmpeg         Spotify API      Genius API
     │
     ▼
 YouTube Audio

               │
               ▼
      Waveform Generation
               │
               ▼
          Redis Cache
```

---

# Project Structure

```text
NoctuneBackend
│
├── Server.py              # FastAPI application
├── Download.py            # Download pipeline
├── Waveform.py            # Waveform extraction
├── Redis.py               # Playlist management
├── redis_cache.py         # Redis caching
├── spotify_meta.py        # Spotify metadata
├── HashMap.py
├── config/
├── requirements.txt
└── README.md
```

---

# Technology Stack

| Technology | Purpose |
|------------|----------|
| FastAPI | Backend API |
| Python | Core application |
| yt-dlp | Audio extraction |
| FFmpeg | Audio transcoding |
| Redis | Caching |
| AsyncPG | Database connectivity |
| WebSockets | Download progress |
| Genius API | Lyrics |
| Mutagen | Audio metadata |

---

# Streaming Pipeline

```text
Client Request
      │
      ▼
FastAPI Endpoint
      │
      ▼
yt-dlp extracts audio URL
      │
      ▼
FFmpeg transcodes stream
      │
      ▼
StreamingResponse
      │
      ▼
Noctune Player
```

---

# Download Pipeline

```text
User downloads song
        │
        ▼
yt-dlp downloads audio
        │
        ▼
Embed metadata
        │
        ▼
Download album artwork
        │
        ▼
Attach ID3 tags
        │
        ▼
Notify client through WebSocket
```

---

# Installation

## Clone the repository

```bash
git clone https://github.com/krishnanx/NoctunePython.git
cd NoctunePython
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file containing:

```env
SUPABASE_URL=
SUPABASE_KEY=
REDIS_HOST=
REDIS_PORT=
GENIUS_API_TOKEN=
```

## Start Redis

```bash
redis-server
```

## Run the server

```bash
uvicorn Server:app --reload
```

---

# API Highlights

| Endpoint | Description |
|----------|-------------|
| `/stream` | Stream music |
| `/download` | Download tracks |
| `/lyrics` | Fetch lyrics |
| Playlist APIs | Manage playlists |
| Migration APIs | Import Spotify playlists |

---

# Future Improvements

- Authentication
- Background task queue
- Adaptive bitrate streaming
- Audio caching
- Recommendation engine
- Search indexing
- Docker deployment
- Kubernetes support

---

# Author

**Krishnan E**

GitHub: https://github.com/krishnanx

---

# License

This project is open source and intended for educational and personal use.
