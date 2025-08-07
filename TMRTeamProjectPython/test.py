from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# 요소가 로드될 때까지 기다리는 함수
def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


# 요소들이 일정 개수 이상 로드될 때까지 기다리는 함수
def wait_for_elements(driver, by, value, min_count=1, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(by, value)) >= min_count
    )
    return driver.find_elements(by, value)


# 부모 요소 안에서 자식 요소를 기다리는 함수
def wait_for_child_element(parent_element, by, value, timeout=10):
    return WebDriverWait(parent_element, timeout).until(
        lambda el: el.find_element(by, value)
    )


def wait_for_child_elements(parent_element, by, value, min_count=1, timeout=10):
    WebDriverWait(parent_element, timeout).until(
        lambda el: len(el.find_elements(by, value)) >= min_count
    )
    return parent_element.find_elements(by, value)

driver = webdriver.Chrome()
driver.get("https://new.land.naver.com/offices?ms=37.52139,126.931083,16&a=SG&e=RETAIL")
time.sleep(5)

# 🧩 매물 아이템 div 리스트
item_divs = wait_for_elements(driver, By.CSS_SELECTOR, "div.item")

for i in range(len(item_divs)):
    try:
        # ❗ 매번 새로 가져오기 (클릭 후 DOM이 갱신되므로)
        item_divs = wait_for_elements(driver, By.CSS_SELECTOR, "div.item")
        item_divs[i].click()

        # 우측 상세 패널 로딩 대기
        price_line = wait_for_element(driver, By.CSS_SELECTOR, "div.price_line")
        price_type = wait_for_child_element(price_line, By.CLASS_NAME, "type").text
        price_text = wait_for_child_element(price_line, By.CLASS_NAME, "price").text.strip()

        print(f"{i+1}번 매물")
        print(f"  💰 {price_type}: {price_text}")
        print("-" * 40)

    except Exception as e:
        print(f"[❌ 실패] {i+1}번 매물: {e}")
        continue

driver.quit()
