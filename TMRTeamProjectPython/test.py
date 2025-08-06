import json
import time
from seleniumwire import webdriver

driver = webdriver.Chrome()
driver.get("https://new.land.naver.com/offices?ms=37.5205561,126.9267056,16&a=SG&e=RETAIL&v=NOLOAN")
driver.implicitly_wait(5)

# 매물번호 수집
article_nos = []
for request in driver.requests:
    if request.response and "api/articles?" in request.url:
        try:
            data = json.loads(request.response.body.decode('utf-8'))
            article_nos = [a.get("articleNo") for a in data.get("articleList", [])]
        except:
            pass
        break

# ✅ 브라우저에서 fetch로 상세 정보 요청 (Selenium JS 실행)
for article_no in article_nos:
    url = f"https://new.land.naver.com/api/articles/{article_no}?complexNo=&realEstateType=SG"

    js_code = f"""
        return fetch("{url}", {{
            method: "GET",
            headers: {{
                "Referer": "https://new.land.naver.com/"
            }}
        }}).then(res => res.json())
        .catch(e => {{ return {{error: e.toString()}} }});
    """

    try:
        detail = driver.execute_script(js_code)
        print(f"\n📦 Raw Response for {article_no}:")
        print(json.dumps(detail, indent=2, ensure_ascii=False))

        article_data = detail.get("article", {})  # ✨ 중첩 구조

        lat = article_data.get("latitude")
        lng = article_data.get("longitude")
        deposit = article_data.get("price", {}).get("deposit")
        rent_price = article_data.get("price", {}).get("rentPrice")
        area = article_data.get("areaInfo", {}).get("supplySpace")
        area1 = article_data.get("areaInfo", {}).get("exclusiveSpace")

        print(f"📌 매물번호: {article_no}")
        print(f"📍 위치: ({lat}, {lng})")
        print(f"🏠 공급면적: {area}㎡ / 전용면적: {area1}㎡")
        print(f"💰 보증금: {deposit} / 월세: {rent_price}")
        print("-" * 40)

    except Exception as e:
        print(f"[❌ JS 요청 실패] 매물번호 {article_no}: {e}")


    time.sleep(0.3)

driver.quit()
