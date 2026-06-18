# Playlist Importer

![Python](https://img.shields.io/badge/Python-3670A0?style=flat&logo=python&logoColor=ffdd54)
![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white)
![Spotify](https://img.shields.io/badge/Spotify-1DB954?style=flat&logo=spotify&logoColor=white)
![YouTube Music](https://img.shields.io/badge/YouTube_Music-FF0000?style=flat&logo=youtubemusic&logoColor=white)

A minimalist web app that **transfers playlists between YouTube Music and Spotify — in both directions**. Point it at a playlist on one service and it recreates it on the other, matching each track as closely as it can.

![Playlist Importer](https://github.com/SurajBhari/playlist-importer/assets/45149585/2cce5bd3-7075-4f4f-938e-0da17f3d4de6)

## How it works

- **Spotify** access via [`spotipy`](https://github.com/spotipy-dev/spotipy) (OAuth, with playlist-modify scopes).
- **YouTube Music** access via [`ytmusicapi`](https://github.com/sigma67/ytmusicapi) (`oauth.json`).
- Tracks are read from the source playlist, searched on the destination service, and added to a new playlist. Results stream back to the page as the transfer runs.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Create a Spotify app and put your `app_id` / `app_secret` in `config.py` (redirect URI `http://localhost:5000/callback`).
3. Generate `oauth.json` for YouTube Music (`ytmusicapi oauth`).
4. Run it:
   ```bash
   python main.py
   ```

Open the local site, authenticate, paste a playlist, and pick the direction to convert.
