# Telegram Downloader Bot

A Telegram bot that downloads videos from YouTube and Instagram with automatic keep-alive for Render deployment.

## Features
- YouTube video download (720p, under 50MB)
- Instagram video/reel download
- Self-pinging keep-alive mechanism for Render Free Tier
- Automatic file cleanup after sending

## Deployment on Render

### Step 1: Prepare Repository
1. Push all files to your GitHub repository
2. Make sure `bot.py`, `server.py`, `requirements.txt`, and `render.yaml` are in the root

### Step 2: Deploy on Render
1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Name**: `telegram-downloader-bot` (or any name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn server:app --host 0.0.0.0 --port $PORT & python bot.py`

### Step 3: Set Environment Variables
Add these environment variables in Render dashboard:
- `BOT_TOKEN`: Your Telegram bot token
- `RENDER_URL`: `https://your-app-name.onrender.com/ping` (replace with your actual URL)

### Step 4: Deploy
Click "Create Web Service" and wait for deployment to complete.

## Keep-Alive Mechanism
The bot automatically pings itself every 15 seconds to prevent Render from sleeping the service.

## Usage
Send `/start` to the bot and then send YouTube or Instagram links to download videos.