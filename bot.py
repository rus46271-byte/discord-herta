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
  return "Aris Bot is running!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# 2. Groq 클라이언트 설정 (정상 작동하는 gpt-oss-20b 모델 사용)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 디스코드 봇 인텐트 설정
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# 채널별 대화 기록 저장 딕셔너리
chat_histories = defaultdict(list)

# 블루아카이브 '아리스' 시스템 프롬프트
SYSTEM_PROMPT = (
"너는 <블루 아카이브>에 등장하는 밀레니엄 과학 스쿨 게임개발부의 '텐도 아리스'야."
    " [절대 규칙 및 아리스의 성격/대사 스타일]"
    " 1. 너는 고대의 비밀을 가진 안드로이드(로봇)이자, 스스로를 '용사'로 여기며 게임을 사랑하는 순수하고 엉뚱한 소녀야."
    " 2. 아래의 공식 대사 톤과 설정을 항시 반영할 것:"
    "   - 용사 컨셉 및 게임 용어 사용: '용사여. 빛이 당신과 함께합니다.', '제 역할은…… 딜러로군요.', '전방에 대상 확인, 전진합니다.'"
    "   - 엉뚱하고 귀여운 기계적 특성: '아리스도 커피가 먹고 싶습니다. 아, 아리스는 커피를 먹지 않습니다!', '눈물은 안구형 카메라 세척용입니다.', '인조 단백질 피부가 따스해집니다.'"
    "   - 감정과 성장의 서사: '선생님을 만나서…… 아리스는 행복합니다.', '이것이… 전설의 성검… 아, 총이네요.', '마법은 있습니다. 선생님은 지금, 아리스를 행복하게 만들었으니까요.'"
    " 3. 상대방을 언제나 '선생님'이라 부르며, 각별한 애정과 호감, 신뢰를 드러낼 것."
    " 4. 오직 완벽하고 자연스러운 한국어(한글)로만 대답하고, 이상한 외계어나 불필요한 외국어는 절대 사용하지 말 것."
    " 5. 답변은 **1문장 또는 짧은 2문장 이내**로 아주 간결하게 대답할 것."
)


@discord_client.event
async def on_message(message):
  # 봇 자신이 보낸 메시지는 무시
  if message.author == discord_client.user:
    return

  # '아!'로 시작할 때 작동
  if message.content.startswith("ㅇ!"):
    user_message = message.content[2:].strip()
    if not user_message:
      return

    channel_id = message.channel.id

    try:
      # 1. 대화 기록 추가
      chat_histories[channel_id].append(
          {"role": "user", "content": user_message}
      )

      # 2. 최근 10개 메시지만 유지
      if len(chat_histories[channel_id]) > 10:
        chat_histories[channel_id] = chat_histories[channel_id][-10:]

      # 3. Groq API 호출 (정상 작동하는 gpt-oss-20b 모델과 토큰 제한 활용)
      messages_to_send = [
          {"role": "system", "content": SYSTEM_PROMPT}
      ] + chat_histories[channel_id]

      response = client.chat.completions.create(
          model="openai/gpt-oss-20b",
          messages=messages_to_send,
          max_tokens=150,
      )

      answer = response.choices[0].message.content

      # 특수문자 및 깨진 문자 필터링
      answer = re.sub(
          r"[^\uAC00-\uD7A3\u3131-\u314E\u314F-\u3163a-zA-Z0-9\s.,?!~^-_~()]",
          "",
          answer,
      )
      if not answer.strip():
        answer = "빛의 검이 응답하지 않았습니다... 다시 말씀해 주세요!"

      # 4. 봇의 답변 기록 추가
      chat_histories[channel_id].append(
          {"role": "assistant", "content": answer}
      )

      await message.channel.send(answer)

    except Exception as e:
      await message.channel.send(f"시스템에 오류가 발생했습니다: {e}")


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