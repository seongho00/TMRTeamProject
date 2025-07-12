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
            first_category = li_button.text.strip()
            li_button.click()
            print(f"{idx}번째 버튼 텍스트:", li_button.text.strip())

            category_second_ul = wait_for_child_element(category_wrapper, By.XPATH, ".//dd/ul[2]")

            category_second_li_count = wait_for_child_elements(category_second_ul, By.TAG_NAME, "li")
            print("li2 개수:", len(category_second_li_count))

            # ✅ 2차 li 순회
            for li2_idx, li2 in enumerate(category_second_li_count[1:], start=2):

                # 2번째부터
                if li2_idx != 2:
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
                    # 상세 카테고리 선택
                    second_button = li2.find_element(By.TAG_NAME, "button")
                    sec_category = second_button.text.strip()
                    second_button.click()

                    # 결과 버튼 누르기
                    box_class = wait_for_element(driver, By.CLASS_NAME, "boxSearch")
                    result_button = box_class.find_element(By.XPATH, "./button")
                    result_button.click()

                    # 데이터 찾아가기
                    table_class = wait_for_element(driver, By.CLASS_NAME, "q-table")
                    tbody_class = table_class.find_element(By.TAG_NAME, "tbody")
                    tr_class = wait_for_child_elements(tbody_class, By.TAG_NAME, "tr")

                    # 3차 순회
                    for tr in tr_class[2:]:
                        try:
                            td = tr.find_elements(By.TAG_NAME, "td")

                            # 4차 순회
                            # 순서 : 행정구역, 유동인구수, 업소수, 남성인구수, 여성인구수, 10대, 20대, 30대, 40대, 50대, 60대이상인구
                            print(li_button.text.strip())

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

                            # 1번쨰 카테고리
                            print("1번째 버튼 텍스트:" + first_category)

                            # 2번쨰 카테고리
                            print("2번째 버튼 텍스트:" + sec_category)

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
                            print(f"3번째 오류 발생: {e3}")

                except Exception as e2:
                    print(f"2번째 오류 발생: {e2}")


        except Exception as e:
            print(f"{idx}번째 li에서 오류 발생:", e)

driver.quit()
