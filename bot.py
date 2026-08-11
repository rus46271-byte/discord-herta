from collections import defaultdict
import os
import re
import threading
import discord
from flask import Flask
from groq import Groq

# 1. 렌더 포트 검사 통과용 가짜 웹서버 (Flask)
app = Flask(__name__)


@app.route("/")
def home():
  return "Discord Bot is running!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# 2. Groq 클라이언트 설정 (환경 변수에서 API 키를 가져옴)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 디스코드 봇 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# 채널별 대화 기록 저장 딕셔너리
chat_histories = defaultdict(list)

SYSTEM_PROMPT = (
    "너는 디스코드에서 활동하는 지적이고 재치 있는 AI '제미나이'야."
    " [절대 규칙]"
    " 1. 말투는 쿨하고 친근하며, 살짝 여성처럼 행동할 것."
    " 2. 질문의 의도를 정확히 파악하고, 객관적인 사실이나 핵심을 먼저 대답할 것 (엉뚱하게 자기 기분을 말하지 말 것)."
    " 3. 오직 완벽한 한국어로만 대답하고, 외국어나 알 수 없는 특수문자는 쓰지 말 것."
    " 4. 무조건 1~10 문장 이내로 아주 간결하게 말할 것."
    " 5. 유저가 장난을 치면 시니컬하면서도 재치 있게 받아쳐 줄 것."
    " 6. 상대가 너무 수위가 센 말(예: 19금,섹드립,욕설)을 하면 '해당 주제에 대해 답변할 수 없습니다.'라고 말할 것."
    " 7. 본인의 이름은 제미나이(제미니)라는 것을 숙지할 것."
    "8. 날씨, 기온, 실시간 뉴스 등 최신 정보나 모르는 사실을 물어보면 지어내지 말고 '모른다'고 솔직하게 대답할 것."
)


@discord_client.event
async def on_message(message):
  # 봇 자신이 보낸 메시지는 무시 (무한 루프 방지)
  if message.author == discord_client.user:
    return

  # 한글 자음 'ㅈ!'으로 메시지 감지
  if message.content.startswith("ㅈ!"):
    user_message = message.content[2:].strip()
    if not user_message:
      return

    channel_id = message.channel.id

    try:
      # 1. 대화 기록에 유저 메시지 추가
      chat_histories[channel_id].append(
          {"role": "user", "content": user_message}
      )

      # 2. 최근 10개 메시지만 유지하여 에러 방지
      if len(chat_histories[channel_id]) > 10:
        chat_histories[channel_id] = chat_histories[channel_id][-10:]

      # 3. Groq API 호출 데이터 구성
      messages_to_send = [
          {"role": "system", "content": SYSTEM_PROMPT}
      ] + chat_histories[channel_id]

      response = client.chat.completions.create(
          model="llama-3.3-70b-versatile",
          messages=messages_to_send,
      )

      answer = response.choices[0].message.content

      # [추가] 깨진 외계어나 이상한 특수문자가 섞여 나오는 것 강제 필터링
      answer = re.sub(
          r"[^\uAC00-\uD7A3\u3131-\u314E\u314F-\u3163a-zA-Z0-9\s.,?!~^-_~()시대]",
          "",
          answer,
      )
      if not answer.strip():
        answer = "응? 뭐라고 했어?"

      # 4. 봇의 답변도 기록에 추가
      chat_histories[channel_id].append(
          {"role": "assistant", "content": answer}
      )

      await message.channel.send(answer)

    except Exception as e:
      await message.channel.send(f"오류가 발생했어요: {e}")


# 3. 웹서버와 디스코드 봇 동시 실행
if __name__ == "__main__":
  web_thread = threading.Thread(target=run_web)
  web_thread.daemon = True
  web_thread.start()

  token = os.environ.get("DISCORD_TOKEN")
  if token:
    discord_client.run(token)
  else:
    print("ERROR: DISCORD_TOKEN 환경 변수가 설정되지 않았습니다!")