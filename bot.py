import os
import asyncio
import logging
import requests
import re
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
import yt_dlp
import instaloader
try:
    from pytube import YouTube
    PYTUBE_AVAILABLE = True
except ImportError:
    PYTUBE_AVAILABLE = False

# --- CONFIGURATION ---
# Get token from environment variable (for security on Render)
TOKEN = os.getenv("BOT_TOKEN", "8029734237:AAHnRdsX62F_ZLipk4TTq-nN1igpugSd6e8")
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Render URL for self-pinging (will be set after deployment)
RENDER_URL = os.getenv("RENDER_URL", "https://your-app-name.onrender.com/ping")

# Setup logging
logging.basicConfig(level=logging.INFO)

# --- HELPER FUNCTIONS ---
def extract_video_id(url):
    """Extract YouTube video ID from URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

# --- DOWNLOADER FUNCTIONS ---

async def download_tiktok(url, message: types.Message):
    status_msg = await message.reply("⏳ Downloading TikTok video...")
    
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'best[ext=mp4][filesize<50M]/best[filesize<50M]/best',
        'noplaylist': True,
        'quiet': True,
    }
    
    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        if filename and os.path.exists(filename):
            file_size = os.path.getsize(filename) / (1024 * 1024)
            
            if file_size > 50:
                await status_msg.edit_text(f"❌ Video is too big ({file_size:.1f}MB).")
                os.remove(filename)
            else:
                await status_msg.edit_text("Uploading... 🚀")
                await message.reply_video(
                    video=types.FSInputFile(filename), 
                    caption=f"✅ {info.get('title', 'TikTok Video')}\n🤖 @Reebuddybot"
                )
                os.remove(filename)
                await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Could not download this TikTok video.")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ TikTok Error: {str(e)}")
        if filename and os.path.exists(filename):
            os.remove(filename)

async def download_twitter(url, message: types.Message):
    status_msg = await message.reply("⏳ Downloading Twitter video...")
    
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'best[ext=mp4][filesize<50M]/best[filesize<50M]/best',
        'noplaylist': True,
        'quiet': True,
    }
    
    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        if filename and os.path.exists(filename):
            file_size = os.path.getsize(filename) / (1024 * 1024)
            
            if file_size > 50:
                await status_msg.edit_text(f"❌ Video is too big ({file_size:.1f}MB).")
                os.remove(filename)
            else:
                await status_msg.edit_text("Uploading... 🚀")
                await message.reply_video(
                    video=types.FSInputFile(filename), 
                    caption=f"✅ {info.get('title', 'Twitter Video')}\n🤖 @Reebuddybot"
                )
                os.remove(filename)
                await status_msg.delete()
        else:
            await status_msg.edit_text("❌ Could not download this Twitter video.")
            
    except Exception as e:
        await status_msg.edit_text(f"❌ Twitter Error: {str(e)}")
        if filename and os.path.exists(filename):
            os.remove(filename)

async def download_youtube(url, message: types.Message):
    status_msg = await message.reply("⚡ YouTube has become very restrictive lately...")
    
    # Provide helpful alternatives instead of failing
    video_id = extract_video_id(url)
    
    await status_msg.edit_text(
        "🚫 **YouTube Download Currently Unavailable**\n\n"
        "YouTube has implemented strict bot detection that blocks most download attempts.\n\n"
        "**Alternative Solutions:**\n"
        "• Use Instagram/TikTok links instead (they work!)\n"
        "• Try @SaveVideoBot or @YTSaveBot\n"
        "• Use online tools like y2mate.com\n"
        "• Download on your phone with apps like Snaptube\n\n"
        "**This bot works great with:**\n"
        "✅ Instagram Reels\n"
        "✅ TikTok videos\n"
        "✅ Twitter videos\n"
        "✅ Facebook videos\n\n"
        "Sorry for the inconvenience! 😔"
    )

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

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    await message.answer(
        "🆘 **Help & FAQ**\n\n"
        "**Why doesn't YouTube work?**\n"
        "YouTube has implemented very strict bot detection that blocks most automated downloads. This affects all download bots, not just ours.\n\n"
        "**What works perfectly:**\n"
        "✅ Instagram Reels & Posts\n"
        "✅ TikTok videos\n"
        "✅ Twitter/X videos\n"
        "✅ Facebook videos\n\n"
        "**For YouTube videos, try:**\n"
        "• @SaveVideoBot\n"
        "• @YTSaveBot\n"
        "• Online tools like y2mate.com\n"
        "• Mobile apps like Snaptube\n\n"
        "**Usage:** Just send me a link!\n"
        "**File limit:** 50MB max\n"
        "**Bot by:** @Reebuddybot"
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 **Welcome to Multi-Platform Video Downloader!**\n\n"
        "**Supported Platforms:**\n"
        "✅ Instagram (Reels & Posts)\n"
        "✅ TikTok\n"
        "✅ Twitter/X\n"
        "✅ Facebook\n"
        "⚠️ YouTube (Currently restricted)\n\n"
        "**Just send me a link and I'll download it for you!**\n\n"
        "🤖 @Reebuddybot"
    )

@dp.message(F.text)
async def handle_link(message: types.Message):
    url = message.text.strip()
    
    if "youtube.com" in url or "youtu.be" in url:
        await download_youtube(url, message)
    elif "instagram.com" in url:
        await download_instagram(url, message)
    elif "tiktok.com" in url or "vm.tiktok.com" in url:
        await download_tiktok(url, message)
    elif "twitter.com" in url or "x.com" in url or "t.co" in url:
        await download_twitter(url, message)
    elif "facebook.com" in url or "fb.watch" in url:
        await download_twitter(url, message)  # Facebook uses same method as Twitter
    else:
        await message.reply(
            "🤔 **Unsupported Platform**\n\n"
            "**Supported platforms:**\n"
            "✅ Instagram\n"
            "✅ TikTok\n" 
            "✅ Twitter/X\n"
            "✅ Facebook\n"
            "⚠️ YouTube (Currently restricted)\n\n"
            "Please send a link from one of these platforms!"
        )

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
    try:
        # Create downloads folder if it doesn't exist
        if not os.path.exists("downloads"):
            os.makedirs("downloads")
        
        # Test connection to Telegram API
        print("🔄 Testing connection to Telegram...")
        me = await bot.get_me()
        print(f"✅ Connected successfully! Bot: @{me.username}")
        
        # Start keep-alive loop in background (only on Render)
        if os.getenv("RENDER"):
            asyncio.create_task(keep_alive())
            print("🔄 Keep-alive started for Render deployment")
        
        print("🤖 Bot is online and ready!")
        await dp.start_polling(bot)
        
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check your internet connection")
        print("2. Verify bot token is correct")
        print("3. Try running on Render instead of locally")
        print("4. Check if VPN/firewall is blocking Telegram")

if __name__ == "__main__":
    asyncio.run(main())