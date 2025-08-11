import pandas as pd
import pymysql
from pymysql.cursors import DictCursor

# ====== 설정 ======
CSV_PATH = "C:\\Users\\qjvpd\\OneDrive\\바탕 화면\\위험도_예측결과_20251.csv"

DB_HOST = "localhost"
DB_PORT = 3306
DB_USER = "root"
DB_PASS = ""
DB_NAME = "TMRTeamProject"

# ====== 1) CSV 로드 ======
df = pd.read_csv(CSV_PATH)

# 컬럼 명 매핑(실제 CSV에 맞춰 확인)
# ['행정동_코드','행정동_코드_명','서비스_업종_코드','서비스_업종_코드_명','위험도_점수','위험도','위험도7','예측_위험도']

# ====== 정규화 (0~100, 18 이상은 계산에서만 제외) ======
mask = df["위험도_점수"] < 9  # 18 이상 제외

# min/max는 18 미만 데이터만 사용
min_v = df.loc[mask, "위험도_점수"].min()
max_v = df.loc[mask, "위험도_점수"].max()
denom = (max_v - min_v) if max_v != min_v else 1

# 18 미만인 데이터만 계산
df.loc[mask, "risk100_all"] = ((df.loc[mask, "위험도_점수"] - min_v) / denom * 100).round(1)

df.loc[df["위험도_점수"] >= 9, "risk100_all"] = 100


def norm_group(g):
    gmin, gmax = g.min(), g.max()
    d = (gmax - gmin) if gmax != gmin else 1
    return ((g - gmin) / d * 100).round(1)

df["risk100_by_biz"] = df.groupby("서비스_업종_코드")["위험도_점수"].transform(norm_group)

# ====== 3) DB 연결 및 UPSERT ======
conn = pymysql.connect(
    host=DB_HOST, port=DB_PORT, user=DB_USER, password=DB_PASS,
    db=DB_NAME, charset="utf8mb4", cursorclass=DictCursor, autocommit=False
)


upsert_sql = """
INSERT INTO risk_score (
  emd_cd, reg_date, update_date, upjong_cd,
  risk_raw, risk_label, risk7_label, risk_pred,
  risk100_all, risk100_by_biz
) VALUES (
  %(emd_cd)s, NOW(), NOW(), %(upjong_cd)s,
  %(risk_raw)s, %(risk_label)s, %(risk7_label)s, %(risk_pred)s,
  %(risk100_all)s, %(risk100_by_biz)s
)
ON DUPLICATE KEY UPDATE
  update_date     = NOW(),
  risk_raw        = VALUES(risk_raw),
  risk_label      = VALUES(risk_label),
  risk7_label     = VALUES(risk7_label),
  risk_pred       = VALUES(risk_pred),
  risk100_all     = VALUES(risk100_all),
  risk100_by_biz  = VALUES(risk100_by_biz);
"""

try:
    with conn.cursor() as cur:

        rows = []
        for _, r in df.iterrows():
            rows.append({
                "emd_cd":         str(r["행정동_코드"]),
                "upjong_cd":      str(r["서비스_업종_코드"]),
                "risk_raw":       float(r["위험도_점수"]),
                "risk_label":     int(r["위험도"]) if pd.notnull(r["위험도"]) else None,
                "risk7_label":    str(r["위험도7"]) if pd.notnull(r["위험도7"]) else None,
                "risk_pred":      int(r["예측_위험도"]) if pd.notnull(r["예측_위험도"]) else None,
                "risk100_all":    float(r["risk100_all"]),
                "risk100_by_biz": float(r["risk100_by_biz"]),
            })

        cur.executemany(upsert_sql, rows)
    conn.commit()
    print(f"Upsert 완료: {len(rows)} rows")
except Exception as e:
    conn.rollback()
    raise
finally:
    conn.close()