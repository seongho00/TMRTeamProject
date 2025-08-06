from seleniumwire import webdriver
import json

# 1. 크롬 드라이버 실행
driver = webdriver.Chrome()
driver.get("https://new.land.naver.com/offices?ms=37.5205561,126.9267056,16&a=SG&e=RETAIL&v=NOLOAN")

# 2. API 응답 대기
driver.implicitly_wait(5)

# 3. 네트워크 요청 중 articles API 응답 탐색
for request in driver.requests:
    if request.response and "api/articles?" in request.url:
        try:
            # 4. JSON 데이터 파싱
            data = json.loads(request.response.body.decode('utf-8'))
            articles = data.get('articleList', [])

            # 5. 위도, 경도 출력
            for article in articles:
                print(article.get('articleNo'), article.get('latitude'), article.get('longitude'))
        except Exception as e:
            print(f"[❌ 오류] 응답 파싱 실패: {e}")
        break

driver.quit()
