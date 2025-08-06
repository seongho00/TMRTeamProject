from selenium import webdriver
from selenium.webdriver.common.by import By
import time

article_no = "2542054078"
url = f"https://new.land.naver.com/offices?ms=37.52139,126.931083,16&a=SG&e=RETAIL"

driver = webdriver.Chrome()
driver.get(url)
time.sleep(5)

# page_source 저장해서 클래스명 확인
with open("naver_office_with_detail.html", "w", encoding="utf-8") as f:
    f.write(driver.page_source)

print("✅ 우측 상세창 포함된 HTML 저장됨.")
driver.quit()