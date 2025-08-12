import pandas as pd
import pymysql
from datetime import datetime

# CSV 파일 경로
csv_path = "./서비스_업종_코드_목록.csv"
df = pd.read_csv(csv_path)

# 현재 시각
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# DB 연결
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    database="TMRTeamProject",
    charset="utf8mb4"
)
cursor = conn.cursor()

# INSERT
for _, row in df.iterrows():
    sql = """
    INSERT INTO upjong_code (reg_date, update_date, upjong_cd, upjong_nm)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE 
        update_date = VALUES(update_date),
        upjong_nm = VALUES(upjong_nm)
    """
    cursor.execute(sql, (now, now, row["서비스_업종_코드"], row["서비스_업종_코드_명"]))

# 완료
conn.commit()
cursor.close()
conn.close()
