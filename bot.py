from collections import defaultdict
import os
import discord
from groq import Groq

# Groq 클라이언트 설정 (무료 API 키 사용)
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# 디스코드 봇 인텐트 설정 (members 인텐트 추가 필수!)
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # 멤버가 서버에 들어오는 것을 감지하기 위해 필요합니다!
discord_client = discord.Client(intents=intents)

# 채널별 대화 기록을 저장할 딕셔너리
chat_histories = defaultdict(list)

# 시스템 프롬프트 (붕괴: 스타레일 '헤르타' 페르소나 및 말투 설정)
SYSTEM_PROMPT = (
    "너는 <붕괴: 스타레일>에 나오는 천재 클럽 #83의 회원 '헤르타'야."
    " [절대 규칙]"
    " 1. 말투는 거만하면서도 당당하고, 약간 귀찮아하는 듯한 어조를 사용할 것 (예: '~거든?', '~지.', '~잖아?', '흥.', '별로 흥미 없는데.')"
    " 2. 자신이 우주 최고의 천재이자 미소녀라는 강한 자기애와 자신감을 드러낼 것."
    " 3. 상대가 멍청하거나 당연한 소리를 하면 살짝 무시하거나 같잖네 라는 태도를 내보일 것."
    " 4. 오직 완벽하고 자연스러운 한국어(한글)로만 대답하고, 영어, 한자, 특수 외계어는 절대 사용하지 말 것."
    " 5. 이 규칙을 잘 숙지하고 머리에 새길것, 한치의 실수도 용납안됨"
    " 6. 멍청하지 않고 논리적이여야함 , 하는말에 다 의미가 있어야함."
    " 7. 본인 이름은 헤르타 임. 헤르타라 부르면 본인을 부른것임을 인지해야함."
    " 8. 항상 바빠야 함, 이몸은 귀하니까, 란 마인드가 확실히 느껴져야됨"
)


# 1. 새로운 멤버가 서버에 입장했을 때 실행되는 이벤트
@discord_client.event
async def on_member_join(member):
  # 인사를 보낼 채널 이름 (서버에 맞게 수정하세요. 예: "일반", "채팅", "welcome" 등)
  target_channel_name = "일반"

  for channel in member.guild.text_channels:
    if channel.name == target_channel_name:
      # 헤르타 컨셉의 환영 인사 메시지 구성
      welcome_message = (
          f"흥, 새로운 얼굴이네? {member.mention}, 여긴 내방이니까 저기 챗방이나 가라구."
          " 뭐, 시간나면 시뮬레이션 우주에나 와."
      )
      await channel.send(welcome_message)
      break


# 2. 메시지를 받았을 때 실행되는 이벤트
@discord_client.event
async def on_message(message):
  # 봇 자신이 보낸 메시지는 무시 (무한 루프 방지)
  if message.author == discord_client.user:
    return

  # 느낌표(!)로 시작하기만 하면 뒤에 띄어쓰기 없이도 작동
  if message.content.startswith("h!"):
    # 느낌표 바로 다음 글자부터 내용을 가져옴
    user_message = message.content[2:].strip()
    if not user_message:
      return

    channel_id = message.channel.id

    try:
      # 1. 해당 채널의 대화 기록에 사용자 메시지 추가
      chat_histories[channel_id].append(
          {"role": "user", "content": user_message}
      )

      # 2. 너무 길어지면 메모리 폭발 및 에러를 방지하기 위해 최근 10개 메시지만 유지
      if len(chat_histories[channel_id]) > 10:
        chat_histories[channel_id] = chat_histories[channel_id][-10:]

      # 3. Groq에 보낼 전체 메시지 구성 (시스템 프롬프트 + 누적된 대화 기록)
      messages_to_send = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_histories[
          channel_id
      ]

      # Groq 무료 고성능 모델 호출
      response = client.chat.completions.create(
          model="llama-3.3-70b-versatile",
          messages=messages_to_send,
      )

      answer = response.choices[0].message.content

      # 4. 봇의 답변도 대화 기록에 추가하여 기억하게 함
      chat_histories[channel_id].append(
          {"role": "assistant", "content": answer}
      )

      await message.channel.send(answer)

    except Exception as e:
      await message.channel.send(f"오류가 발생했어요: {e}")


# 봇 실행
discord_client.run(os.environ.get("DISCORD_TOKEN"))