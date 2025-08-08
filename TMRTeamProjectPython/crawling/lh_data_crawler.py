from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time


# ====== 대기 함수 ======
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


# ====== 크롤링 시작 ======
driver = webdriver.Chrome(service=Service("chromedriver.exe"))
driver.get("https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1069")

# 목록 로드 대기
wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=15)

# 페이지당 모든 공고 순회
while True:
    rows = wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=10)

    for idx in range(len(rows)):
        # 매 클릭 전에 다시 목록 요소 새로 가져오기 (stale 방지)
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        link = rows[idx].find_element(By.CSS_SELECTOR, "a")
        print(f"▶ {idx + 1}번째 공고 클릭")
        old = driver.current_url
        link.click()

        # 상세 페이지 로드 대기 (상세 페이지 고유 요소로 바꾸기)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table, .view, .detail"))
        )

        print("✅ 상세페이지 진입 완료")

        data_lis = wait_for_elements(driver, By.CSS_SELECTOR, ".subCntBody .indent .list_st1")

        for li in data_lis:
            text = li.text.strip()
            print(text)


        # 상세 페이지에서 데이터 추출 예시



        WebDriverWait(driver, 10).until(lambda d: d.current_url != old)

        # 뒤로 가기
        driver.back()

        # 다시 목록 로드 대기
        wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=10)
        time.sleep(0.5)  # 서버 부하 방지

    # 페이지네이션: 다음 버튼 클릭
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.page_next")
        if "disabled" in next_btn.get_attribute("class"):
            print("📌 마지막 페이지 도달")
            break
        next_btn.click()
        wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=10)
    except:
        print("📌 다음 버튼 없음, 종료")
        break

driver.quit()
