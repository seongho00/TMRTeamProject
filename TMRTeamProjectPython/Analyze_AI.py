import os

import pymysql

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    db="tmrteamproject",
    charset="utf8mb4"
)
cursor = conn.cursor()

pdf_path = "C:/Users/user/Desktop/TeamProject/SimpAnly/대전광역시 서구 가수원동 편의점.pdf"
file_name = os.path.basename(pdf_path)

region_name, business_type = file_name.replace(".pdf", "").rsplit(" ", 1)

# PDF 파일 열기
with open(pdf_path, 'rb') as f:
    pdf_data = f.read()

cursor.close()
conn.close()
