import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 파일 불러오기
flow_df = pd.read_csv("C:/Users/user/Downloads/서울시 상권분석서비스(길단위인구-행정동).csv", encoding='cp949')
sales_df = pd.read_csv("C:/Users/user/Downloads/서울시 상권분석서비스(추정매출-행정동)_2024년.csv", encoding='cp949')

# 유동인구: 2024년 1분기만 추출 후 행정동별 총합 계산
flow_1q = flow_df[flow_df['기준_년분기_코드'] == 20241]
flow_sum = flow_1q.groupby('행정동_코드')['총_유동인구_수'].sum().reset_index()

# 매출: 2024년 1분기만 추출 후 행정동별 총합 계산
sales_1q = sales_df[sales_df['기준_년분기_코드'] == 20241]
sales_sum = sales_1q.groupby('행정동_코드')['당월_매출_금액'].sum().reset_index()

# 컬럼명 정리 및 병합
flow_sum.rename(columns={'행정동_코드': '행정동코드'}, inplace=True)
sales_sum.rename(columns={'행정동_코드': '행정동코드'}, inplace=True)
merged = pd.merge(flow_sum, sales_sum, on='행정동코드', how='inner')

# 상관계수 및 공분산 계산
correlation = merged['총_유동인구_수'].corr(merged['당월_매출_금액'])
covariance = np.cov(merged['총_유동인구_수'], merged['당월_매출_금액'])[0, 1]

print("상관계수:", correlation)
print("공분산:", covariance)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 산점도 시각화
plt.figure(figsize=(10, 6))
plt.scatter(merged['총_유동인구_수'], merged['당월_매출_금액'], alpha=0.6)
plt.title('유동인구 vs 매출액 (2024년 1분기)')
plt.xlabel('총 유동인구수')
plt.ylabel('당월 매출금액')
plt.grid(True)
plt.tight_layout()
plt.show()

# 분석 결과 CSV로 저장
merged.to_csv("C:/Users/user/Downloads/유동인구_매출_분석결과_2024_1분기.csv", encoding='utf-8-sig')
print("CSV 저장 완료")
