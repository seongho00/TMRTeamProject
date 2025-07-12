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
    service=Service("C:/Users/qjvpd/IdeaProjects/TMRTeamProject/TMRTeamProjectPython/crawling/chromedriver.exe")
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

regions = wait_for_child_elements(region_wrapper, By.XPATH, ".//dd/ul[2]//li")

for jdx, region in enumerate(regions[1:], start=2):

    if jdx != 2:
        # class가 'region'인 버튼 찾기
        region_wrapper = wait_for_element(driver, By.CLASS_NAME, "region")
        region_wrapper.click()
        time.sleep(0.5)
        region.click()

    try:
        # 결과 버튼 누르기
        box_class = wait_for_element(driver, By.CLASS_NAME, "boxSearch")
        result_button = box_class.find_element(By.XPATH, "./button")
        result_button.click()

        # 데이터 찾아가기
        table_class = wait_for_element(driver, By.CLASS_NAME, "q-table")
        tbody_class = table_class.find_element(By.TAG_NAME, "tbody")
        tr_class = wait_for_child_elements(tbody_class, By.TAG_NAME, "tr")

        for tr in tr_class[2:]:
            try:
                td = tr.find_elements(By.TAG_NAME, "td")

                # 시구
                sido_name_list = tr_class[0].find_elements(By.TAG_NAME, "td")
                sido_name = sido_name_list[0].text.strip()
                print("시구 이름 : " + sido_name)

                # 시군구
                sigungu_name_list = tr_class[1].find_elements(By.TAG_NAME, "td")
                sigungu_name = sigungu_name_list[0].text.strip()
                print("시군구 이름 : " + sigungu_name)

                # 행정동
                emd_name = td[0].text.strip()
                print("행정동 이름 : " + emd_name)

                # 총 유동인구수
                total = td[1].text.strip()
                print("총 유동인구수 : " + total)
                # 업소수
                business_cnt = td[2].text.strip()
                print("업소수 : " + business_cnt)
                # 남성인구수
                male = td[3].text.strip()
                print("남성인구수 : " + male)

                # 여성인구수
                female = td[4].text.strip()
                print("여성인구수 : " + female)
                # 10대
                age_10 = td[5].text.strip()
                print("10대 : " + age_10)
                # 20대
                age_20 = td[6].text.strip()
                print("20대 : " + age_20)
                # 30대
                age_30 = td[7].text.strip()
                print("30대 : " + age_30)
                # 40대
                age_40 = td[8].text.strip()
                print("40대 : " + age_40)
                # 50대
                age_50 = td[9].text.strip()
                print("50대 : " + age_50)
                # 60대이상인구
                age_60 = td[9].text.strip()
                print("60대 : " + age_60)


            except Exception as e3:
                print(f"2번째 오류 발생: {e3}")

    except Exception as e2:
        print(f"1번째 오류 발생: {e2}")

driver.quit()
