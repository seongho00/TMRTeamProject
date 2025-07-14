import requests
import pymysql
import pandas as pd
import time

# 업종 대분류 코드 매핑
major_category_codes = {
    "소매": "G2", "음식": "I2", "수리/개인": "S2",
    "과학/기술": "M1", "예체능": "R1", "교육": "P1",
    "부동산": "L1", "숙박": "I1", "보건의료": "Q1", "관리/임대": "N1"
}

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    db="TMRTeamProject",
    charset="utf8mb4"
)

cursor = conn.cursor()
cursor.execute("SELECT emd_cd FROM admin_dong;")
rows = cursor.fetchall()

# 대분류 → 중분류 업종 리스트 요청
def get_mid_categories(major_code):
    url = "https://bigdata.sbiz.or.kr/gis/api/getTpbizMclCodeWithBest.json"
    params = {"tpbizLclcd": major_code}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

for row in rows:
    adminCd = row[0]
    try:
        print(f"[요청 중] admiCd: {adminCd}")



    except Exception as e:
        print(f"[오류 발생] {adminCd}: e")
        time.sleep(3)