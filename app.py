import os
import threading
from flask import Flask

# 디스코드 봇 파일을 임포트해서 백그라운드 스레드로 실행
import bot

app = Flask(__name__)


@app.route("/")
def home():
  return "Discord Bot is running!"


def run_discord_bot():
  # bot.py에 있는 discord_client를 실행
  bot.discord_client.run(os.environ.get("DISCORD_TOKEN"))


if __name__ == "__main__":
  # 1. 별도의 스레드에서 디스코드 봇 실행
  bot_thread = threading.Thread(target=run_discord_bot)
  bot_thread.daemon = True
  bot_thread.start()

  # 2. 렌더 웹 서버 유지용 Flask 실행
  app.run(host="0.0.0.0", port=10000)