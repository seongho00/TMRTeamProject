from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import time

from selenium.webdriver.support.wait import WebDriverWait


# 요소가 로드될 때까지 기다리는 함수
def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


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


# 아이디 : By.ID
# 클래스 : By.CLASS_NAME
# value : By.XPATH

# ChromeDriver 경로 설정
driver = webdriver.Chrome(
    service=Service("C:/Users/admin/IdeaProjects/TMRTeamProject/TMRTeamProjectPython/chromedriver.exe"))

# 접속할 URL
driver.get("https://bigdata.sbiz.or.kr/#/sbiz/sttus/dynpplSttus")

# # class가 'region'인 버튼 찾기
# region_wrapper = wait_for_element(driver, By.CLASS_NAME, "region")
# region_wrapper.click()
#
# # region_wrapper 내부에서 '대전광역시' 버튼 찾기
# daejeon_btn = wait_for_child_element(region_wrapper, By.XPATH, ".//button[text()='대전광역시']")
# daejeon_btn.click()
#
# All_btn = wait_for_child_element(region_wrapper, By.XPATH, ".//dd/ul[2]//button[text()='전체']")
# All_btn.click()

# class가 'category'인 버튼 찾기
category_wrapper = wait_for_element(driver, By.CLASS_NAME, "category")
category_wrapper.click()

category_ul = wait_for_child_element(category_wrapper, By.XPATH, ".//dd/ul[1]")

category_li_count = category_ul.find_elements(By.TAG_NAME, "li")
print("li 개수:", len(category_li_count))

for idx, li in enumerate(category_li_count, start=2):
    try:
        li_button = li.find_element(By.TAG_NAME, "button")
        print(f"{idx}번째 버튼 텍스트:", li_button.text.strip())
        li_button.click()

        category_second_ul = wait_for_child_element(category_wrapper, By.XPATH, ".//dd/ul[2]")

        category_second_li_count = category_second_ul.find_elements(By.TAG_NAME, "li")

        # ✅ 2차 li 순회
        for jdx, li2 in enumerate(category_second_li_count, start=2):
            try:
                second_button = li2.find_element(By.TAG_NAME, "button")
                print(f"    [{idx}-{jdx}] 2차 버튼 클릭: {second_button.text.strip()}")
                second_button.click()
                time.sleep(1)  # 클릭 후 로딩 대기

                # 👉 이 자리에 크롤링 또는 데이터 수집 작업 가능

            except Exception as e2:
                print(f"    [{idx}-{jdx}] 2차 li 오류:", e2)

    except Exception as e:
        print(f"{idx}번째 li에서 오류 발생:", e)


time.sleep(2)

driver.quit()
