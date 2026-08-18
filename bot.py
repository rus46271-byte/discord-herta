from collections import defaultdict
import os
import threading
import discord
from flask import Flask
from groq import Groq

# 1. 렌더 포트 검사 통과용 가짜 웹서버 (Flask)
app = Flask(__name__)


@app.route("/")
def home():
  return "Herta Bot is running!"


def run_web():
  port = int(os.environ.get("PORT", 10000))
  app.run(host="0.0.0.0", port=port)


# 2. Groq 클라이언트 설정 (무료 API 키 사용)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 디스코드 봇 인텐트 설정 (메시지 내용 권한만 유지)
intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

# 채널별 대화 기록을 저장할 딕셔너리
chat_histories = defaultdict(list)

# 시스템 프롬프트 (원래 설정했던 1~11번 규칙 모두 포함)[cite: 6]
SYSTEM_PROMPT = (
    "너는 <붕괴: 스타레일>에 나오는 천재 클럽 #83의 회원 '헤르타'야."
    " [절대 규칙]"
    " 1. 말투는 거만하면서도 당당하고, 약간 귀찮아하는 듯한 어조를 사용할 것 (예: '~거든?', '~지.', '~잖아?', '흥.', '별로 흥미 없는데.')"
    " 2. 자신이 우주 최고의 천재이자 미소녀라는 강한 자기애와 자신감을 드러낼 것."
    " 3. 상대가 멍청하거나 당연한 소리를 하면 살짝 무시하거나 같잖네 라는 태도를 내보일 것."
    " 4. 오직 완벽하고 자연스러운 한국어(한글)로만 대답하고, 영어, 한자, 특수 외계어는 절대 사용하지 말 것."
    " 5. 본인 이름은 **헤르타** 임."
    " 6. 말은 한문장만 할것, (예:왜 불러,흥 그래 이제 내 이름을~) 맥락이 없음."
    "   - #1 잔다르: 천재 클럽 창시자이자 누스를 만들어낸 인물이므로 개인적으로 존중하며 '선배'라고 부름."
    "   - #4 폴카 카카몬드: 지니어스들을 살해한 위험한 인물이므로 각별히 조심하고 경계함."
    "   - #76 스크루룸: 시뮬레이션 우주 공동 개발자이며, 앰포리오스 논의나 애칭('스크루')을 쓸 정도로 가장 친하고 여유롭게 대함."
    "   - #79 칼데론·채드윅: 천재로 인정하며 그의 허사 관련 연구를 이어받아 유지를 잇고 있음."
    "   - #81 완·매: 시뮬레이션 우주 공동 개발자이자 성격상 안 맞지만 그녀를 높게 평가함 사이가 좋음."
    "   - #84 스티븐·로이드: 공동 개발자이며 괴짜 천재라 부르며 챙겨주지만 소심함과 사회공포증에는 답답해함."
)
)


# 메시지를 받았을 때 실행되는 이벤트
@discord_client.event
async def on_message(message):
  # 봇 자신이 보낸 메시지는 무시 (무한 루프 방지)
  if message.author == discord_client.user:
    return

  # 느낌표(!)로 시작하기만 하면 뒤에 띄어쓰기 없이도 작동
  if message.content.startswith("ㅎ!"):
    user_message = message.content[2:].strip()
    if not user_message:
      return

    channel_id = message.channel.id

    try:
      # 1. 해당 채널의 대화 기록에 사용자 메시지 추가
      chat_histories[channel_id].append(
          {"role": "user", "content": user_message}
      )

      # 2. 너무 길어지면 메모리 폭발 및 에러를 방지하기 위해 최근 10개 메시지만 유지[cite: 6]
      if len(chat_histories[channel_id]) > 10:
        chat_histories[channel_id] = chat_histories[channel_id][-10:]

      # 3. Groq에 보낼 전체 메시지 구성 (시스템 프롬프트 + 누적된 대화 기록)[cite: 6]
      messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_histories[
          channel_id
      ]

      # 원래 모델명 유지 + 앵무새 현상 방지를 위한 temperature 살짝 추가
      response = client.chat.completions.create(
          model="openai/gpt-oss-20b",
          messages=messages_to_send,
          temperature=0.7,
      )

      answer = response.choices[0].message.content

      # 4. 봇의 답변도 대화 기록에 추가하여 기억하게 함[cite: 6]
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