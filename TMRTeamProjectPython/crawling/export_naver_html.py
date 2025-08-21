import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

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

article_no = "2542054078"
url = f"https://new.land.naver.com/offices?ms=37.52139,126.931083,16&a=SG&e=RETAIL"

driver = webdriver.Chrome()
driver.get(url)
time.sleep(5)

item_divs = driver.find_elements(By.CSS_SELECTOR, "div.item")
item_divs[0].click()
time.sleep(1)

# 상세 정보 패널 로딩 대기
wait_for_element(driver, By.CSS_SELECTOR, "div.price_line")  # or 다른 확실한 요소

# page_source 저장해서 클래스명 확인
with open("naver_office_with_detail.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

print("✅ 우측 상세창 포함된 HTML 저장됨.")
driver.quit()
