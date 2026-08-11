import os
import threading
from flask import Flask
import bot

app = Flask(__name__)

@app.route("/")
def home():
    return "Discord Bot is running!"

def run_discord_bot():
    token = os.environ.get("DISCORD_TOKEN")
    if token:
        bot.discord_client.run(token)

if __name__ == "__main__":
    # 1. 백그라운드 스레드에서 디스코드 봇 실행
    bot_thread = threading.Thread(target=run_discord_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # 2. 렌더가 요구하는 포트(10000번)로 Flask 웹서버 즉시 실행
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)