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
    service=Service("C:/Users/qjvpd/IdeaProjects/TMRTeamProject/TMRTeamProjectPython/chromedriver.exe")
)
# 접속할 URL
driver.get("https://bigdata.sbiz.or.kr/#/sbiz/sttus/dynpplSttus")

# class가 'region'인 버튼 찾기
region_wrapper = wait_for_element(driver, By.CLASS_NAME, "region")
region_wrapper.click()

# region_wrapper 내부에서 '대전광역시' 버튼 찾기
daejeon_btn = wait_for_child_element(region_wrapper, By.XPATH, ".//button[text()='대전광역시']")
daejeon_btn.click()

All_btn = wait_for_child_element(region_wrapper, By.XPATH, ".//dd/ul[2]//button[text()='대덕구']")
All_btn.click()

# 여기서부터 다시 시작해야함

# class가 'category'인 버튼 찾기
category_wrapper = wait_for_element(driver, By.CLASS_NAME, "category")
category_wrapper.click()

time.sleep(0.5)

category_ul = wait_for_child_element(category_wrapper, By.XPATH, ".//dd/ul[1]")

category_li = category_ul.find_elements(By.TAG_NAME, "li")

regions = wait_for_child_elements(region_wrapper, By.XPATH, ".//dd/ul[2]//li")

for jdx, region in enumerate(regions[1:], start=2):

    if jdx != 2:
        # class가 'region'인 버튼 찾기
        region_wrapper = wait_for_element(driver, By.CLASS_NAME, "region")
        region_wrapper.click()
        time.sleep(0.5)
        category_ul = wait_for_child_element(category_wrapper, By.XPATH, ".//dd/ul[1]")
        region.click()

    for idx, li in enumerate(category_li[1:], start=2):
        try:

            # ✅ 반복마다 카테고리 열기
            category_wrapper = wait_for_element(driver, By.CLASS_NAME, "category")
            category_wrapper.click()
            time.sleep(0.5)

            # 카테고리 목록 다시 참조
            category_ul = wait_for_child_element(category_wrapper, By.XPATH, ".//dd/ul[1]")
            category_li = category_ul.find_elements(By.TAG_NAME, "li")
            li = category_li[idx - 1]  # 현재 idx에 해당하는 li 재조회

            li_button = li.find_element(By.TAG_NAME, "button")
            li_button.click()
            print(f"{idx}번째 버튼 텍스트:", li_button.text.strip())

            category_second_ul = wait_for_child_element(category_wrapper, By.XPATH, ".//dd/ul[2]")

            category_second_li_count = wait_for_child_elements(category_second_ul, By.TAG_NAME, "li")
            print("li2 개수:", len(category_second_li_count))

            # ✅ 2차 li 순회
            for li2_idx, li2 in enumerate(category_second_li_count[1:], start=2):

                # 2번째부터
                if li2_idx != 2 :
                    # ✅ 반복마다 카테고리 열기
                    category_wrapper = wait_for_element(driver, By.CLASS_NAME, "category")
                    category_wrapper.click()
                    time.sleep(0.5)

                    # 카테고리 목록 다시 참조
                    category_ul = wait_for_child_element(category_wrapper, By.XPATH, ".//dd/ul[1]")
                    category_li = category_ul.find_elements(By.TAG_NAME, "li")
                    li = category_li[idx - 1]  # 현재 idx에 해당하는 li 재조회

                    li_button = li.find_element(By.TAG_NAME, "button")
                    li_button.click()

                try:
                    second_button = li2.find_element(By.TAG_NAME, "button")
                    second_button.click()
                    box_class = wait_for_element(driver, By.CLASS_NAME, "boxSearch")
                    result_button = box_class.find_element(By.XPATH, "./button")
                    result_button.click()

                    table_class = wait_for_element(driver, By.CLASS_NAME, "q-table")
                    tbody_class = table_class.find_element(By.TAG_NAME, "tbody")
                    tr_class = wait_for_child_elements(tbody_class, By.TAG_NAME, "tr")

                    # 3차 순회
                    for tr in tr_class[2:]:
                        try:
                            td = tr.find_elements(By.TAG_NAME, "td")

                            # 4차 순회
                            for data in td:
                                try:
                                    value = data.text.strip()
                                    print(value)

                                except Exception as e4:
                                    print(f"4번째 오류 발생: {e4}")

                        except Exception as e3:
                            print(f"3번째 오류 발생: {e3}")

                except Exception as e2:
                    print(f"2번째 오류 발생: {e2}")


        except Exception as e:
            print(f"{idx}번째 li에서 오류 발생:", e)

driver.quit()
