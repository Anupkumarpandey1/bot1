#!/usr/bin/env python3
"""
Simple connection test for Telegram bot
"""
import requests
import asyncio
from aiogram import Bot

# Your bot token
TOKEN = "8029734237:AAHnRdsX62F_ZLipk4TTq-nN1igpugSd6e8"

def test_basic_connection():
    """Test basic internet connectivity"""
    print("🔄 Testing basic internet connection...")
    try:
        response = requests.get("https://httpbin.org/ip", timeout=10)
        print(f"✅ Internet works! Your IP: {response.json()['origin']}")
        return True
    except Exception as e:
        print(f"❌ Internet connection failed: {e}")
        return False

def test_telegram_api():
    """Test Telegram API connectivity"""
    print("🔄 Testing Telegram API connection...")
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['ok']:
                print(f"✅ Telegram API works! Bot: @{data['result']['username']}")
                return True
            else:
                print(f"❌ Bot token invalid: {data}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Telegram API connection failed: {e}")
        return False

async def test_aiogram():
    """Test aiogram library"""
    print("🔄 Testing aiogram library...")
    try:
        bot = Bot(token=TOKEN)
        me = await bot.get_me()
        print(f"✅ Aiogram works! Bot: @{me.username}")
        await bot.session.close()
        return True
    except Exception as e:
        print(f"❌ Aiogram failed: {e}")
        return False

async def main():
    print("🧪 Bot Connection Test\n")
    
    # Test 1: Basic internet
    if not test_basic_connection():
        print("\n❌ Fix your internet connection first!")
        return
    
    print()
    
    # Test 2: Telegram API
    if not test_telegram_api():
        print("\n❌ Telegram API not accessible!")
        print("💡 Try:")
        print("   • Check if Telegram is blocked in your country")
        print("   • Try using a VPN")
        print("   • Check firewall/antivirus settings")
        return
    
    print()
    
    # Test 3: Aiogram
    if not await test_aiogram():
        print("\n❌ Aiogram library has issues!")
        print("💡 Try:")
        print("   • pip install --upgrade aiogram")
        print("   • Restart your terminal")
        return
    
    print("\n🎉 All tests passed! Your bot should work fine.")
    print("💡 If it still fails locally, deploy to Render - it will work there!")

if __name__ == "__main__":
    asyncio.run(main())