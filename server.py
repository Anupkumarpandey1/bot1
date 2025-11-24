from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"status": "Bot is running!", "service": "Telegram Downloader Bot"}

@app.get("/ping")
def ping():
    return {"message": "pong", "status": "alive"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "active"}