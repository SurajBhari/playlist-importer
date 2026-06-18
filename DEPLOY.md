# Deploying playlist-importer

This app ships ready to deploy on a free host (Render, Railway, Fly.io, …). A `Dockerfile`, `Procfile`, and `render.yaml` are included.

## Option A — Render free tier (easiest)

1. Go to https://render.com → **New → Web Service** → connect this repo.
2. Render auto-detects `render.yaml` — click **Apply**.
   Manual settings if needed:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn main:app --bind 0.0.0.0:$PORT --timeout 120`
3. Deploy. You get a public `*.onrender.com` URL.

## Option B — Docker (Railway / Fly.io / any host)

```bash
docker build -t playlist-importer .
docker run -p 8080:8080 playlist-importer
```

The container listens on `$PORT` (defaults to 8080).

## ⚠️ Required configuration

Needs a `config.py` with Spotify `app_id`/`app_secret`, and a YouTube Music `oauth.json`. Set the Spotify redirect URI to your deployed URL + `/callback`.
