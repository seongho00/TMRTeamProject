import pandas as pd
import pymysql

# 엑셀 파일 경로
excel_path = "upjong_code.xlsx"

# 엑셀 불러오기
df = pd.read_excel(excel_path, skiprows=2)  # 앞 2줄은 헤더로 간주하지 않음

# 컬럼명 정리
df.columns = ["major_cd", "major_nm", "middle_cd", "middle_nm", "minor_cd", "minor_nm"]

# MySQL 연결
conn = pymysql.connect(
    host="database-1.c72qauo6szew.ap-northeast-2.rds.amazonaws.com",
    user="admin",
    password="tk123412345!!",
    database="SHW",
    charset="utf8mb4"
)

cursor = conn.cursor()

# INSERT
sql = """
      INSERT INTO upjong_code (major_cd, major_nm, middle_cd, middle_nm, minor_cd, minor_nm)
      VALUES (%s, %s, %s, %s, %s, %s)
      """

# INSERT 실행
for idx, row in df.iterrows():
    try:
        cursor.execute(sql, tuple(row))
        print(f"[성공] {row['minor_nm']} 삽입 완료")
    except Exception as e:
        print(f"[실패] {row['minor_nm']} 삽입 실패 → {e}")

# 커밋 & 종료
conn.commit()
cursor.close()
conn.close()

print("전체 완료")
