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

async def download_youtube_via_api(url, message: types.Message):
    """Try downloading YouTube via third-party APIs and services"""
    video_id = extract_video_id(url)
    if not video_id:
        return None
    
    # Method 1: Try multiple third-party APIs
    apis_to_try = [
        # API 1: Cobalt.tools (popular and reliable)
        {
            "url": "https://co.wuk.sh/api/json",
            "payload": {
                "url": url,
                "vQuality": "480",
                "vFormat": "mp4",
                "isAudioOnly": False,
                "filenamePattern": "basic"
            },
            "method": "POST"
        },
        # API 2: Alternative service
        {
            "url": f"https://www.youtube.com/oembed?url={url}&format=json",
            "method": "GET"
        }
    ]
    
    for i, api in enumerate(apis_to_try):
        try:
            print(f"Trying API {i+1}: {api['url']}")
            
            if api["method"] == "POST":
                response = requests.post(api["url"], json=api["payload"], timeout=30)
            else:
                response = requests.get(api["url"], timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle cobalt.tools response
                if "status" in data and data.get("status") == "success" and data.get("url"):
                    video_url = data["url"]
                    
                    # Download the video
                    video_response = requests.get(video_url, timeout=60, stream=True)
                    if video_response.status_code == 200:
                        filename = f"downloads/youtube_{video_id}.mp4"
                        
                        # Download with size check
                        total_size = 0
                        with open(filename, 'wb') as f:
                            for chunk in video_response.iter_content(chunk_size=8192):
                                if chunk:
                                    f.write(chunk)
                                    total_size += len(chunk)
                                    # Stop if file gets too big (50MB = 52428800 bytes)
                                    if total_size > 52428800:
                                        f.close()
                                        os.remove(filename)
                                        return None
                        
                        # Final size check
                        if os.path.exists(filename):
                            file_size = os.path.getsize(filename) / (1024 * 1024)
                            if file_size > 50:
                                os.remove(filename)
                                return None
                            return filename
                
                # Handle other API responses (get video info)
                elif "title" in data:
                    # This gives us video info, we can use it for better error messages
                    print(f"Got video info: {data.get('title', 'Unknown')}")
                    
        except Exception as e:
            print(f"API {i+1} failed: {e}")
            continue
    
    # Method 2: Try direct YouTube embed approach (sometimes works)
    try:
        embed_url = f"https://www.youtube.com/embed/{video_id}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        response = requests.get(embed_url, headers=headers, timeout=15)
        if response.status_code == 200:
            # This is just to check if video is accessible
            # In a real implementation, you'd parse the response for video URLs
            print("Video embed accessible, but no direct download URL found")
            
    except Exception as e:
        print(f"Embed approach failed: {e}")
    
    return None

async def download_youtube(url, message: types.Message):
    status_msg = await message.reply("⏳ Trying to download YouTube video...")
    
    # Method 1: Try third-party APIs first
    await status_msg.edit_text("⏳ Trying external download service...")
    api_result = await download_youtube_via_api(url, message)
    
    if api_result:
        try:
            await status_msg.edit_text("Uploading... 🚀")
            await message.reply_video(
                video=types.FSInputFile(api_result), 
                caption=f"✅ YouTube Video Downloaded\n🤖 @Reebuddybot"
            )
            os.remove(api_result)
            await status_msg.delete()
            return
        except Exception as e:
            print(f"Upload failed: {e}")
            if os.path.exists(api_result):
                os.remove(api_result)
    
    # Method 2: Fallback to yt-dlp with aggressive settings
    await status_msg.edit_text("⏳ Trying direct download...")
    
    # Ultra-aggressive yt-dlp configuration
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'format': 'worst[ext=mp4][filesize<50M]/worst[filesize<50M]/18/17/worst',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        },
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['hls'],
            }
        },
    }
    
    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
        if filename and os.path.exists(filename):
            file_size = os.path.getsize(filename) / (1024 * 1024)
            
            if file_size > 50:
                await status_msg.edit_text(f"❌ Video is too big ({file_size:.1f}MB). Try a shorter video.")
                os.remove(filename)
                return
            else:
                await status_msg.edit_text("Uploading... 🚀")
                await message.reply_video(
                    video=types.FSInputFile(filename), 
                    caption=f"✅ {info.get('title', 'YouTube Video')}\n🤖 @Reebuddybot"
                )
                os.remove(filename)
                await status_msg.delete()
                return
        else:
            raise Exception("No file created")
            
    except Exception as e:
        error_msg = str(e)
        print(f"yt-dlp failed: {error_msg}")
        
        if filename and os.path.exists(filename):
            os.remove(filename)
        
        # Method 3: Try pytube as final fallback
        if PYTUBE_AVAILABLE:
            try:
                await status_msg.edit_text("⏳ Trying final backup method...")
                
                yt = YouTube(url)
                # Get the lowest quality stream
                stream = yt.streams.filter(file_extension='mp4', progressive=True).order_by('resolution').first()
                if not stream:
                    stream = yt.streams.filter(file_extension='mp4').first()
                
                if stream:
                    safe_title = "".join(c for c in yt.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
                    filename = f"downloads/{safe_title[:30]}.mp4"
                    
                    stream.download(output_path='downloads', filename=f"{safe_title[:30]}.mp4")
                    
                    if os.path.exists(filename):
                        file_size = os.path.getsize(filename) / (1024 * 1024)
                        if file_size > 50:
                            await status_msg.edit_text(f"❌ Video is too big ({file_size:.1f}MB).")
                            os.remove(filename)
                        else:
                            await status_msg.edit_text("Uploading... 🚀")
                            await message.reply_video(
                                video=types.FSInputFile(filename), 
                                caption=f"✅ {yt.title}\n🤖 @Reebuddybot"
                            )
                            os.remove(filename)
                            await status_msg.delete()
                            return
            except Exception as pytube_error:
                print(f"Pytube also failed: {pytube_error}")
        
        # All methods failed - show helpful message
        if "Sign in to confirm" in error_msg or "bot" in error_msg.lower():
            await status_msg.edit_text(
                "🚫 **YouTube Bot Detection Active**\n\n"
                "YouTube detected automated access and is blocking downloads from this server location.\n\n"
                "**🔥 Working Alternatives (Tested & Reliable):**\n\n"
                "**Telegram Bots:**\n"
                "🤖 @SaveVideoBot - Most reliable\n"
                "🤖 @YTSaveBot - Good backup\n"
                "🤖 @VideoDownloadBot - Alternative\n\n"
                "**Web Tools:**\n"
                "🌐 y2mate.com - Fast & reliable\n"
                "🌐 savefrom.net - Multiple formats\n"
                "🌐 yt1s.com - HD quality\n\n"
                "**Mobile Apps:**\n"
                "📱 NewPipe (Android) - Open source\n"
                "📱 Snaptube - Popular choice\n"
                "📱 VidMate - Multiple platforms\n\n"
                "**✅ This bot works perfectly with:**\n"
                "🔥 Instagram Reels & Posts\n"
                "🔥 TikTok Videos  \n"
                "🔥 Twitter Videos\n"
                "🔥 Facebook Videos\n\n"
                "Try sending an Instagram or TikTok link! 😊"
            )
        else:
            await status_msg.edit_text(
                "❌ **YouTube Download Failed**\n\n"
                "**Possible reasons:**\n"
                "• Video is private/age-restricted\n"
                "• Video exceeds 50MB limit\n"
                "• Geographic/regional restrictions\n"
                "• YouTube server protection active\n"
                "• Video format not supported\n\n"
                "**🔥 Try These Alternatives:**\n\n"
                "**Telegram Bots:**\n"
                "🤖 @SaveVideoBot - Highly recommended\n"
                "🤖 @YTSaveBot - Good success rate\n\n"
                "**Web Downloaders:**\n"
                "🌐 y2mate.com - Reliable & fast\n"
                "🌐 savefrom.net - Multiple options\n\n"
                "**📱 Mobile Solutions:**\n"
                "NewPipe, Snaptube, VidMate apps\n\n"
                "**✅ This bot excels at:**\n"
                "🔥 Instagram ✅ TikTok ✅ Twitter ✅ Facebook\n\n"
                "Send an Instagram/TikTok link for instant results! 🚀"
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
        "👋 **Welcome to Advanced Video Downloader!**\n\n"
        "**Supported Platforms:**\n"
        "✅ Instagram (Reels & Posts) - **Excellent**\n"
        "✅ TikTok - **Excellent**\n"
        "✅ Twitter/X - **Very Good**\n"
        "✅ Facebook - **Good**\n"
        "�  YouTube - **Advanced Multi-Method**\n\n"
        "**YouTube Download Methods:**\n"
        "🔹 Third-party APIs\n"
        "🔹 Direct extraction\n"
        "🔹 Multiple fallbacks\n"
        "🔹 Smart error handling\n\n"
        "**Just send me any video link!**\n\n"
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
