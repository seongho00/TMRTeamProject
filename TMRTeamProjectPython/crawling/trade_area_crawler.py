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



# ✅ Chrome 옵션 설정: 창 크기 조절
options = webdriver.ChromeOptions()
options.add_argument("window-size=1600,1000")  # 원하는 크기로 조절 (예: 1600x1000)

# ✅ ChromeDriver 실행 (경로 설정 포함)
driver = webdriver.Chrome(
    service=Service("chromedriver.exe"),
    options=options
)


# 접속할 URL
driver.get("https://bigdata.sbiz.or.kr/#/hotplace/gis")

# ✅ iframe 전환
iframes = driver.find_elements(By.TAG_NAME, "iframe")
print(f"iframe 개수: {len(iframes)}")





# 하나씩 탐색하며 listCategory가 있는 iframe 찾기
found = False
for idx, iframe in enumerate(iframes):
    try:
        driver.switch_to.frame(iframe)
        WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, "listCategory"))
        )
        print(f"✅ listCategory 요소를 iframe[{idx}]에서 찾음")
        found = True
        break
    except:
        driver.switch_to.default_content()  # 다시 메인 프레임으로 돌아감

search_input = driver.find_element(By.ID, "searchAddress")
search_input.clear()
search_input.send_keys("서울 강남구")


# ✅ listCategory ul 요소 로드 대기
try:
    category_ul = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "listCategory"))
    )
    print("✅ listCategory ul 요소 찾음")

    # ✅ 첫 번째 li 요소 안의 button 클릭
    li_elements = category_ul.find_elements(By.TAG_NAME, "li")
    if li_elements:
        first_button = li_elements[0].find_element(By.TAG_NAME, "button")
        first_button.click()
        print("✅ 첫 번째 li의 버튼 클릭 완료")

        time.sleep(5)
    else:
        print("❌ li 요소가 없습니다.")

except Exception as e:
    print("❌ 에러 발생:", e)


