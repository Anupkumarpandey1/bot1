import os
import asyncio
import logging
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import yt_dlp
import instaloader

# --- CONFIGURATION ---
# Get token from environment variable (for security on Render)
TOKEN = os.getenv("BOT_TOKEN", "8029734237:AAHnRdsX62F_ZLipk4TTq-nN1igpugSd6e8")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Render URL for self-pinging (will be set after deployment)
RENDER_URL = os.getenv("RENDER_URL", "https://your-app-name.onrender.com/ping")

# Setup logging
logging.basicConfig(level=logging.INFO)

# --- DOWNLOADER FUNCTIONS ---

async def download_youtube(url, message: types.Message):
    status_msg = await message.reply("⏳ Finding a video under 50MB (720p)...")
    
    # SETTINGS: Force 720p or lower, and strictly under 50MB + bypass bot detection
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'best[ext=mp4][height<=720][filesize<50M] / best[ext=mp4][height<=480][filesize<50M] / worst[ext=mp4]',
        'noplaylist': True,
        # Anti-bot detection headers
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Accept-Encoding': 'gzip,deflate',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '300',
            'Connection': 'keep-alive',
        },
        # Additional anti-detection options
        'extractor_args': {
            'youtube': {
                'skip': ['hls', 'dash'],
                'player_skip': ['js'],
            }
        },
        # Retry options
        'retries': 3,
        'fragment_retries': 3,
        'sleep_interval': 1,
        'max_sleep_interval': 5,
    }
    
    filename = None
    try:
        # Run the download with anti-bot detection
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        # Check if file exists and check size
        if filename and os.path.exists(filename):
            file_size = os.path.getsize(filename) / (1024 * 1024) # Convert bytes to MB
            
            if file_size > 50:
                await status_msg.edit_text(f"❌ Video is too big ({file_size:.1f}MB). Telegram limit is 50MB.")
                os.remove(filename)
            else:
                await status_msg.edit_text("Uploading... 🚀")
                await message.reply_video(
                    video=types.FSInputFile(filename), 
                    caption=f"✅ {info.get('title', 'Video')}\nResolution: 720p (or best fit)\n🤖 @Reebuddybot"
                )
                os.remove(filename) # Delete file from laptop after sending
                await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Could not download a suitable format under 50MB.")
            
    except Exception as e:
        error_msg = str(e)
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            # Try alternative method for bot-detected videos
            try:
                await status_msg.edit_text("⏳ Trying alternative method...")
                
                # Simplified options for bot-detected videos
                simple_opts = {
                    'outtmpl': 'downloads/%(title)s.%(ext)s',
                    'format': 'worst[ext=mp4]/worst',
                    'noplaylist': True,
                    'quiet': True,
                    'no_warnings': True,
                }
                
                with yt_dlp.YoutubeDL(simple_opts) as ydl:
                    info = ydl.extract_info(url, download=True)
                    filename = ydl.prepare_filename(info)
                    
                if filename and os.path.exists(filename):
                    file_size = os.path.getsize(filename) / (1024 * 1024)
                    if file_size > 50:
                        await status_msg.edit_text(f"❌ Video is too big ({file_size:.1f}MB). Try a shorter video.")
                        os.remove(filename)
                    else:
                        await status_msg.edit_text("Uploading... 🚀")
                        await message.reply_video(
                            video=types.FSInputFile(filename), 
                            caption=f"✅ {info.get('title', 'Video')}\n🤖 @Reebuddybot"
                        )
                        os.remove(filename)
                        await status_msg.delete()
                else:
                    await status_msg.edit_text("❌ Could not download this video. YouTube may have restricted it.")
                    
            except Exception as e2:
                await status_msg.edit_text("❌ YouTube has restricted this video. Try another link or a different video.")
        else:
            await status_msg.edit_text(f"❌ Error: {error_msg}")
            
        if filename and os.path.exists(filename):
            os.remove(filename)

async def download_instagram(url, message: types.Message):
    status_msg = await message.reply("⏳ Fetching Instagram content...")
    L = instaloader.Instaloader()
    
    try:
        # Extract shortcode from URL
        if "/p/" in url:
            shortcode = url.split("/p/")[1].split("/")[0]
        elif "/reel/" in url:
            shortcode = url.split("/reel/")[1].split("/")[0]
        else:
            shortcode = None

        if shortcode:
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            
            if post.is_video:
                video_url = post.video_url
                await message.reply_video(video=video_url, caption="✅ Downloaded via @Reebuddybot")
            else:
                 await message.reply("❌ Currently only supporting Video/Reels.")
        else:
            await message.reply("❌ Could not find post ID in link.")
             
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(f"❌ Instagram Error (Link might be private): {str(e)}")

# --- BOT HANDLERS ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("👋 Hi! Send me a **YouTube** or **Instagram** link.")

@dp.message(F.text)
async def handle_link(message: types.Message):
    url = message.text.strip()
    
    if "youtube.com" in url or "youtu.be" in url:
        await download_youtube(url, message)
    elif "instagram.com" in url:
        await download_instagram(url, message)
    else:
        await message.reply("Please send a valid YouTube or Instagram link.")

# --- KEEP ALIVE FUNCTION ---
async def keep_alive():
    """Self-ping to keep Render service awake"""
    while True:
        try:
            response = requests.get(RENDER_URL, timeout=10)
            print("✅ Pinged Render to stay awake!")
        except Exception as e:
            print(f"❌ Ping error: {e}")
        
        await asyncio.sleep(15)  # Ping every 15 seconds

# --- MAIN ---
async def main():
    # Create downloads folder if it doesn't exist
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    
    # Start keep-alive loop in background
    asyncio.create_task(keep_alive())
    
    print("🤖 Bot is online and keep-alive started...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())