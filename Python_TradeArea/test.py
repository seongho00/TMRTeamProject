import requests
from bs4 import BeautifulSoup

url = "https://bigdata.sbiz.or.kr/#/hotplace/gis"  # 실제 대상 URL로 수정 필요
session = requests.Session()
response = session.get(url)

soup = BeautifulSoup(response.text, "html.parser")

# 대분류 추출
major_category = soup.select_one("dl.step1 ul.listCategory li button.active").text.strip()

# 중분류 추출
middle_category = [
    btn.text.strip()
    for btn in soup.select("dl.step2 ul.listCategorySub li button")
]

# 소분류 추출
minor_category = [
    btn.text.strip()
    for btn in soup.select("dl.step3 ul.listCategorySub li button")
]

result = {
    "대분류": major_category,
    "중분류": middle_category,
    "소분류": minor_category
}

print(result)
