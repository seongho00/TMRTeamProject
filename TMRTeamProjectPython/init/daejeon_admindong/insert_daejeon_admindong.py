import xml.etree.ElementTree as ET
import pandas as pd
import pymysql

tree = ET.parse("행정동데이터.json")  # 실제로는 XML
root = tree.getroot()

rows = []
for item in root.findall(".//item"):
    if item.find("ctprvnNm").text == "대전광역시":
        rows.append({
            "admi_nm": f"{item.find('ctprvnNm').text} {item.find('signguNm').text} {item.find('adongNm').text}",
            "sido_cd": item.find("ctprvnCd").text,
            "sido_nm": item.find("ctprvnNm").text,
            "sgg_cd": item.find("signguCd").text,
            "sgg_nm": item.find("signguNm").text,
            "emd_cd": item.find("adongCd").text,
            "emd_nm": item.find("adongNm").text
        })

df = pd.DataFrame(rows)

print(df.head())  # 또는 df.to_string(index=False)

# MySQL 연결
conn = pymysql.connect(
    host="database-1.c72qauo6szew.ap-northeast-2.rds.amazonaws.com",
    user="admin",
    password="tk123412345!!",
    database="SHW",
    charset="utf8mb4"
)

cursor = conn.cursor()
cursor.execute("SELECT DATABASE();")
print("현재 연결된 DB:", cursor.fetchone())

cursor.execute("SHOW TABLES;")
print("📂 테이블 목록:", cursor.fetchall())

cursor.execute("SHOW CREATE TABLE admin_dong;")
print("🧱 테이블 구조:", cursor.fetchone())

sql = """
INSERT INTO admin_dong (
    admi_nm, sido_cd, sido_nm, sgg_cd, sgg_nm, emd_cd, emd_nm
) VALUES (%s, %s, %s, %s, %s, %s, %s)
"""

for _, row in df.iterrows():
    cursor.execute(sql, (
        row["admi_nm"], row["sido_cd"], row["sido_nm"],
        row["sgg_cd"], row["sgg_nm"], row["emd_cd"], row["emd_nm"]
    ))

conn.commit()
conn.close()
print("✅ DB 저장 완료")
