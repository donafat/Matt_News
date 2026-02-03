import os
import time
import requests
import feedparser # RSS 파싱 라이브러리
from datetime import datetime, timedelta
from dateutil import parser # 날짜 변환용

# =========================================================
# 1. 설정 (형님의 관심사 키워드)
# =========================================================
KEYWORDS = [
    "전고체 배터리",
    "미국 주식",
    "NVDA 엔비디아",
    "갤럭시 S26",
    "전기차 보조금",
    "파이썬 자동화"
]

# 몇 시간 전 뉴스까지 가져올지 설정 (매일 2번 실행한다면 12시간 추천)
TIME_LIMIT_HOURS = 12 

# =========================================================
# 2. 텔레그램 전송 함수
# =========================================================
def send_telegram(message):
    token = os.environ.get('NEW_TELEGRAM_TOKEN')
    chat_id = os.environ.get('NEW_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ 토큰이나 채팅방 ID가 없습니다.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {
        'chat_id': chat_id, 
        'text': message, 
        'parse_mode': 'Markdown',
        'disable_web_page_preview': 'true' # 링크 미리보기 끔 (깔끔하게)
    }
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"전송 실패: {e}")

# =========================================================
# 3. 구글 뉴스 RSS 검색 함수
# =========================================================
def get_google_news(keyword):
    # 구글 뉴스 RSS 주소 (한국어 설정)
    encoded_keyword = requests.utils.quote(keyword)
    rss_url = f"https://news.google.com/rss/search?q={encoded_keyword}&hl=ko&gl=KR&ceid=KR:ko"
    
    feed = feedparser.parse(rss_url)
    news_list = []
    
    # 현재 시간 기준 설정
    now = datetime.now().astimezone() 
    limit_time = now - timedelta(hours=TIME_LIMIT_HOURS)

    print(f"🔍 [{keyword}] 검색 중...")

    for entry in feed.entries[:10]: # 키워드당 최대 10개만 확인
        try:
            # 기사 발행 시간 파싱
            pub_date = parser.parse(entry.published)
            
            # 지정한 시간(예: 12시간) 이내의 기사만 통과
            if pub_date >= limit_time:
                title = entry.title
                link = entry.link
                
                # 출처(신문사)가 제목에 있으면 깔끔하게 정리
                if "-" in title:
                    source = title.split("-")[-1].strip()
                    title = title.rsplit("-", 1)[0].strip()
                else:
                    source = "뉴스"

                news_list.append(f"• [{source}] [{title}]({link})")
        except:
            continue
            
    return news_list

# =========================================================
# 메인 실행
# =========================================================
if __name__ == "__main__":
    print("🚀 뉴스 수집 시작...")
    
    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    full_message = f"📰 *[맞춤 뉴스 브리핑]*\n📅 {today}\n(최근 {TIME_LIMIT_HOURS}시간 내 기사)\n\n"
    has_news = False

    for keyword in KEYWORDS:
        articles = get_google_news(keyword)
        if articles:
            full_message += f"📌 *#{keyword}*\n"
            full_message += "\n".join(articles)
            full_message += "\n\n"
            has_news = True
        else:
            print(f"  -> '{keyword}' 관련 새 뉴스 없음")

    full_message += "------------------\n💡 Google News 기반"

    if has_news:
        print("✅ 뉴스 있음, 전송 중...")
        # 메시지가 너무 길면 나눠서 보내기 (텔레그램 제한 대비)
        if len(full_message) > 4000:
            send_telegram(full_message[:4000])
            send_telegram(full_message[4000:])
        else:
            send_telegram(full_message)
    else:
        print("📭 새로운 뉴스가 없습니다.")
        # (선택) 뉴스 없어도 알림 받고 싶으면 아래 주석 해제
        # send_telegram(f"📭 {today}\n지정된 키워드의 새로운 뉴스가 없습니다.")
