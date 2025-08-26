# plot_risk100_all_hist_db.py
import pandas as pd
import pymysql
import matplotlib.pyplot as plt

# ===== DB 접속 정보 =====
DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = ""
DB_NAME = "TMRTeamProject"

# (선택) 특정 업종/지역만 보고 싶으면 여기에 조건 추가
# ex) WHERE risk100_all IS NOT NULL AND upjong_cd='CS100001' AND emd_cd='11110515'
SQL = """
SELECT risk100_all
FROM risk_score
WHERE risk100_all IS NOT NULL
"""

# ===== DB → DataFrame =====
conn = pymysql.connect(
    host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
    db=DB_NAME, charset="utf8mb4"
)
df = pd.read_sql(SQL, conn)
conn.close()

if df.empty:
    print("조회 결과가 없습니다. SQL 조건을 확인하세요.")
    raise SystemExit()

# ===== 1) 일반 히스토그램 =====
plt.figure(figsize=(8, 5))
plt.hist(df["risk100_all"].dropna(), bins=50)  # 0~100 범위에서 분포 확인
plt.title("risk100_all 분포 (일반 스케일)")
plt.xlabel("risk100_all")
plt.ylabel("빈도")
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.show()

# ===== 2) 로그 스케일 히스토그램 (꼬리/스파이크 확인용) =====
plt.figure(figsize=(8, 5))
plt.hist(df["risk100_all"].dropna(), bins=50)
plt.yscale("log")
plt.title("risk100_all 분포 (Y축 로그 스케일)")
plt.xlabel("risk100_all")
plt.ylabel("빈도(로그)")
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.show()

# (선택) 요약 통계 출력
print(df["risk100_all"].describe())
