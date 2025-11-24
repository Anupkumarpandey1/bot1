#!/bin/bash
# Start both web server and bot
uvicorn server:app --host 0.0.0.0 --port $PORT &
python bot.py