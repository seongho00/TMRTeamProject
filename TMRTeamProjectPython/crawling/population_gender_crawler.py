from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support import expected_conditions as EC
import time
import pymysql

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


# 숫자 쉼표제거 함수
def clean_number(text):
    return int(text.replace(",", "")) if text else 0


# DB 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',  # 비밀번호 입력
    database='TMRTeamProject',
    charset='utf8mb4'
)

cursor = conn.cursor()

# ChromeDriver 경로 설정
driver = webdriver.Chrome(
    service=Service("chromedriver.exe")
)
# 접속할 URL
driver.get("https://bigdata.sbiz.or.kr/#/sbiz/sttus/dynpplSttus")

# class가 'region'인 버튼 찾기
region_wrapper = wait_for_element(driver, By.CLASS_NAME, "region")
region_wrapper.click()

# region_wrapper 내부에서 '서울특별시' 버튼 찾기
btn = wait_for_child_element(region_wrapper, By.XPATH, ".//button[text()='서울특별시']")
btn.click()

All_btn = wait_for_child_element(region_wrapper, By.XPATH, ".//dd/ul[2]//button[text()='강남구']")
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
        time.sleep(0.5)

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
                total = clean_number(td[1].text.strip())
                print("총 유동인구수 : " + str(total))

                # 남성인구수
                male = clean_number(td[3].text.strip())
                print("남성인구수 : " + str(male))

                # 여성인구수
                female = clean_number(td[4].text.strip())
                print("여성인구수 : " + str(female))
                # 10대
                age_10 = clean_number(td[5].text.strip())
                print("10대 : " + str(age_10))
                # 20대
                age_20 = clean_number(td[6].text.strip())
                print("20대 : " + str(age_20))
                # 30대
                age_30 = clean_number(td[7].text.strip())
                print("30대 : " + str(age_30))
                # 40대
                age_40 = clean_number(td[8].text.strip())
                print("40대 : " + str(age_40))
                # 50대
                age_50 = clean_number(td[9].text.strip())
                print("50대 : " + str(age_50))
                # 60대이상인구
                age_60 = clean_number(td[9].text.strip())
                print("60대 : " + str(age_60))

                # admi_nm으로 emd_cd 가져오기
                admi_nm = f"{sido_name} {sigungu_name} {emd_name}"  # 예: 대전광역시 대덕구 법1동

                cursor.execute("SELECT emd_cd FROM admin_dong WHERE admi_nm = %s", (admi_nm,))
                result = cursor.fetchone()

                # 데이터 DB에 넣기
                if result:
                    emd_cd = result[0]
                    print("읍면동 코드:", emd_cd)

                    # INSERT
                    cursor.execute("""
                        INSERT INTO population_stat (emd_cd, total, male, female, age_10, age_20, age_30, age_40, age_50, age_60)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (emd_cd, total, male, female, age_10, age_20, age_30, age_40, age_50, age_60))
                    conn.commit()

                else:
                    print("지역코드 없음:", admi_nm)

            except Exception as e3:
                print(f"2번째 오류 발생: {e3}")

    except Exception as e2:
        print(f"1번째 오류 발생: {e2}")

driver.quit()