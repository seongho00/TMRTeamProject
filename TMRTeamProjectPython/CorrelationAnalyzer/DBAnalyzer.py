import pymysql
import pandas as pd

# 1. 저장할 CSV 불러오기 (이전에 분석된 결과)
for date in [20241, 20242, 20243, 20244]:
    path = f"C:/Users/user/Downloads/유동인구_매출_분석결과_{date}.csv"
    df = pd.read_csv(path, encoding='utf-8-sig')

    # 2. DB 연결
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='1234',
        database='TMRTeamProject',
        charset='utf8mb4'
    )
    cursor = conn.cursor()

    # 3. INSERT 쿼리 실행
    insert_sql = """
                 INSERT INTO analyzer (year_cd, dong_cd, dong_nm, people, sales)
                 VALUES (%s, %s, %s, %s, %s) \
                 """

    for _, row in df.iterrows():
        cursor.execute(insert_sql, (
            row['기준_년분기_코드'],
            row['행정동_코드'],
            row['행정동_코드_명'],
            int(row['총_유동인구_수']),
            int(row['당월_총_매출_금액'])
        ))

    # 4. 커밋 & 종료
    conn.commit()
    cursor.close()
    conn.close()

    print("데이터베이스 저장 완료")
