from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from webdriver_manager.chrome import ChromeDriverManager

# 크롬 드라이버 설정
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))

driver.get("https://bigdata.sbiz.or.kr/#/hotplace/gis")

search_bar = WebDriverWait(driver,10).until(
    EC.presence_of_element_located((By.ID, "searchAddress"))
)

search_bar.send_keys("대전 동구 효동")
search_bar.send_keys(Keys.ENTER)

time.sleep(5)