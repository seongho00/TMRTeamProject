import os

import matplotlib.pyplot as plt
import pandas as pd

# 윈도우에서 기본 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 파일 불러오기
flow_df = pd.read_csv("C:/Users/user/Downloads/서울시 상권분석서비스(길단위인구-행정동).csv", encoding='cp949')
sales_df = pd.read_csv("C:/Users/user/Downloads/서울시 상권분석서비스(추정매출-행정동)_2024년.csv", encoding='cp949')

# 기준 컬럼
merge_key = ['기준_년분기_코드', '행정동_코드', '행정동_코드_명']

# 분석 결과 저장용
results = []

# 분기 반복
for quarter in [20241, 20242, 20243, 20244]:

    # 분기 필터링
    flow_q = flow_df[
        (flow_df['기준_년분기_코드'] == quarter) &
        (flow_df['행정동_코드_명'] != '둔촌1동')
        ].copy()

    sales_q = sales_df[
        (sales_df['기준_년분기_코드'] == quarter) &
        (sales_df['행정동_코드_명'] != '둔촌1동')
        ].copy()

    # 병합 키 타입 통일
    for df in [flow_q, sales_q]:
        for col in merge_key:
            df[col] = df[col].astype(str)

    # 병합
    merged_df = pd.merge(flow_q, sales_q, on=merge_key, how='left')

    # 저장
    merge_save_path = f"C:/Users/user/Downloads/서울_유동인구_매출_{quarter}.csv"

    if os.path.exists(merge_save_path):
        os.remove(merge_save_path)

    merged_df.to_csv(merge_save_path, encoding='utf-8-sig', index=False)
    print(f"병합 CSV 저장 완료 → {merge_save_path}")
    print(merged_df.columns)
