import os
import time
import requests
import feedparser
from datetime import datetime, timedelta
from dateutil import parser

# =========================================================
# 1. 설정 (형님의 관심사 키워드)
# =========================================================
KEYWORDS = [
   "전고체 배터리",
    "미국 주식",
    "엔비디아",
    "로봇",
    "갤럭시 S26",
    "전기차 보조금",
    "파이썬 자동화",
    
    "코스피",
    "코스닥",
    "상한가",          # '종목' 뺌 (범위 확대)
    "하한가",          # '종목' 뺌
    "국내 특징주",
    
    "트럼프 관세",
    "트럼프 IRA",
    "미국 칩스법",
    "중동 위기",       # '지정학적 리스크' -> '위기'로 변경
    "국제 유가",
    "러우 전쟁"
]
TIME_LIMIT_HOURS = 24 

# =========================================================
# 2. 텔레그램 전송 함수 (에러 확인 강화판)
# =========================================================
def send_telegram(message):
    token = os.environ.get('NEW_TELEGRAM_TOKEN')
    chat_id = os.environ.get('NEW_CHAT_ID')
    
    print(f"🔑 토큰 앞자리 확인: {token[:5]}..." if token else "❌ 토큰 없음")
    print(f"🆔 채팅ID 확인: {chat_id}" if chat_id else "❌ 채팅ID 없음")

    if not token or not chat_id:
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id, 
        'text': message, 
        'parse_mode': 'Markdown',
        'disable_web_page_preview': 'true'
    }
    
    try:
        response = requests.post(url, data=data)
        # 여기가 핵심! 성공/실패 여부를 확실히 출력
        if response.status_code == 200:
            print("✅ 텔레그램 전송 성공! (핸드폰 확인하세요)")
        else:
            print(f"❌ 전송 실패 (에러코드: {response.status_code})")
            print(f"❌ 에러 내용: {response.text}")
    except Exception as e:
        print(f"❌ 연결 에러: {e}")

# =========================================================
# 3. 구글 뉴스 RSS 검색 함수
# =========================================================
def get_google_news(keyword):
    encoded_keyword = requests.utils.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    feed = feedparser.parse(rss_url)
    news_list = []
    
    # 시간대 처리 (timezone 에러 방지)
    now = datetime.now().astimezone()
    limit_time = now - timedelta(hours=TIME_LIMIT_HOURS)

    print(f"🔍 [{keyword}] 검색 중...")

    for entry in feed.entries[:10]:
        try:
            # 날짜 형식이 제각각일 수 있어 예외처리 추가
            if hasattr(entry, 'published'):
                pub_date = parser.parse(entry.published)
                # timezone 정보가 없으면 강제로 할당
                if pub_date.tzinfo is None:
                    pub_date = pub_date.replace(tzinfo=now.tzinfo)
                
                if pub_date >= limit_time:
                    title = entry.title
                    link = entry.link
                    if "-" in title:
                        source = title.split("-")[-1].strip()
                        title = title.rsplit("-", 1)[0].strip()
                    else:
                        source = "뉴스"
                    news_list.append(f"• [{source}] [{title}]({link})")
        except Exception as e:
            continue
            
    return news_list

# =========================================================
# 메인 실행
# =========================================================
# =========================================================
# 메인 실행
# =========================================================
if __name__ == "__main__":
    print("🚀 뉴스 수집 시작...")
    
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_message = f"📰 *[맞춤 뉴스 브리핑]*\n📅 {today}\n(최근 {TIME_LIMIT_HOURS}시간 내 기사)\n\n"
    has_news = False

    for keyword in KEYWORDS:
        # 1. 뉴스 검색
        articles = get_google_news(keyword)
        
        # 2. 내용 추가
        if articles:
            full_message += f"📌 *#{keyword}*\n"
            full_message += "\n".join(articles)
            full_message += "\n\n"
            has_news = True
        else:
            print(f"  -> '{keyword}' 관련 새 뉴스 없음")
            
        # 3. 구글 차단 방지용 휴식 (형님 요청대로 적용!)
        time.sleep(2) 

    full_message += "------------------\n💡 Google News 기반"

    # =========================================================
    # [업그레이드된 전송 로직] : 내용이 아무리 길어도 다 보냅니다
    # =========================================================
    if has_news:
        print(f"✅ 뉴스 발견! (총 길이: {len(full_message)}자) 전송 시작...")
        
        # 메시지가 빌 때까지 계속 반복
        while len(full_message) > 0:
            # 1. 남은 길이가 4000자 이하면 -> 한 방에 보내고 끝냄
            if len(full_message) <= 4000:
                send_telegram(full_message)
                break
            
            # 2. 4000자가 넘으면 -> 적당한 위치에서 자름
            else:
                # 4000자 근처에 있는 '줄바꿈(\n)' 위치를 찾음 (글자 중간에 잘림 방지)
                split_index = full_message[:4000].rfind('\n')
                
                # 줄바꿈을 못 찾았으면 어쩔 수 없이 4000자에서 강제로 자름
                if split_index == -1:
                    split_index = 4000
                
                # 잘라낸 앞부분 전송
                send_telegram(full_message[:split_index])
                
                # 보낸 만큼 제외하고, 남은 내용을 다시 full_message에 담음
                full_message = full_message[split_index:]
                
                # 전송 순서 꼬이지 않게 1초 쉼
                time.sleep(1)
                
    else:
        print("📭 새로운 뉴스가 없습니다.")
