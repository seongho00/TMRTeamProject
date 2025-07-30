import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 윈도우에서 기본 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 부호 깨짐 방지

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

    file_path = f"C:/Users/user/Downloads/서울_유동인구_매출_{quarter}.csv"
    df = pd.read_csv(file_path)

    df = df[['총_유동인구_수', '당월_매출_금액']].dropna()
    print(df['총_유동인구_수'])

    # 상관계수 및 공분산 계산
    correlation = df['총_유동인구_수'].corr(df['당월_매출_금액'])
    covariance = np.cov(df['총_유동인구_수'], df['당월_매출_금액'])[0, 1]

    results.append((quarter, correlation, covariance))

    # 시각화
    plt.figure(figsize=(8, 5))
    plt.scatter(df['총_유동인구_수'], df['당월_매출_금액'], alpha=0.5)
    plt.title(f"{quarter} 유동인구 vs 매출")
    plt.xlabel("총 유동인구 수")
    plt.ylabel("당월 매출 금액")
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# 최종 요약 출력
print("분기별 상관계수 및 공분산 요약:")
for quarter, corr, cov in results:
    print(f"{quarter} 분기 - 상관계수: {corr:.4f}, 공분산: {cov:.2f}")
