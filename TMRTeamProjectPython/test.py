from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# ⛳ 유틸 함수
def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )

def wait_for_elements(driver, by, value, min_count=1, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(by, value)) >= min_count
    )
    return driver.find_elements(by, value)

def wait_for_child_element(parent_element, by, value, timeout=10):
    return WebDriverWait(parent_element, timeout).until(
        lambda el: el.find_element(by, value)
    )

# ✅ 크롬 드라이버 설정
driver = webdriver.Chrome()
driver.get("https://new.land.naver.com/offices?ms=37.52139,126.931083,16&a=SG&e=RETAIL")
time.sleep(3)

# ✅ 스크롤 대상 지정
scroll_target = driver.find_element(By.CSS_SELECTOR, "div.item_list.item_list--article")
scroll_pause = 1

# ✅ 중복 방지용 집합
seen_items = set()

# ✅ 매물 처리 루프
while True:
    # 현재 화면에 보이는 매물들
    item_divs = driver.find_elements(By.CSS_SELECTOR, "div.item")
    new_items_found = False

    for item in item_divs:
        try:
            identifier = item.text.strip()
            if identifier in seen_items:
                continue

            new_items_found = True
            seen_items.add(identifier)

            # 스크롤 이동 후 클릭
            driver.execute_script("arguments[0].scrollIntoView(true);", item)
            time.sleep(0.2)
            item.click()

            # 상세 정보 대기 및 추출
            price_box = wait_for_element(driver, By.CSS_SELECTOR, "div.info_article_price")
            price_type = price_box.find_element(By.CLASS_NAME, "type").text  # ex) 월세
            price_value = price_box.find_element(By.CLASS_NAME, "price").text  # ex) 4,000/230

            # 상세 패널 내 테이블 요소
            detail_table = wait_for_element(driver, By.CSS_SELECTOR, "table.info_table_wrap")
            rows = detail_table.find_elements(By.CSS_SELECTOR, "tr.info_table_item")

            # 원하는 정보 저장용 dict
            detail_info = {}

            for row in rows:
                try:
                    ths = row.find_elements(By.TAG_NAME, "th")
                    tds = row.find_elements(By.TAG_NAME, "td")

                    # ⛔ '매물설명' 행은 건너뛰기
                    if any("매물설명" in th.text for th in ths):
                        continue

                    for th, td in zip(ths, tds):
                        key = th.text.strip()
                        val = td.text.strip()
                        detail_info[key] = val
                except:
                    continue

            print("📋 상세 정보:")
            for k, v in detail_info.items():
                print(f" - {k}: {v}")

            print(f"📌 매물: {price_type} / {price_value}")

        except Exception as e:
            print(f"[❌ 오류] 매물 클릭 또는 추출 실패: {e}")
            continue

    if not new_items_found:
        print("✅ 더 이상 새 매물 없음. 종료.")
        break

    # 스크롤을 조금씩 내려 추가 매물 유도
    driver.execute_script("arguments[0].scrollTop += 800", scroll_target)
    time.sleep(scroll_pause)

print(f"🎉 총 크롤링한 매물 수: {len(seen_items)}")
driver.quit()
