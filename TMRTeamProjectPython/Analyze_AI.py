import os

import pandas as pd

# 파일 불러오기
flow_df = pd.read_csv("C:/Users/user/Downloads/서울시 상권분석서비스(길단위인구-행정동).csv", encoding='cp949')
sales_df = pd.read_csv("C:/Users/user/Downloads/서울시 상권분석서비스(추정매출-행정동)_2024년.csv", encoding='cp949')

# 병합 전 컬럼 비교
print("flow_df columns:", flow_df.columns)
print("sales_df columns:", sales_df.columns)

# 기준 컬럼명
merge_key = ['기준_년분기_코드', '행정동_코드', '행정동_코드_명']

for quarter in [20241, 20242, 20243, 20244]:
    flow_q = flow_df[flow_df['기준_년분기_코드'] == quarter]
    flow_grouped = flow_q.groupby(merge_key, as_index=False).sum()

    print(flow_grouped)

    sales_q = sales_df[sales_df['기준_년분기_코드'] == quarter]

    # 병합
    merged_df = pd.merge(flow_grouped, sales_q, on=merge_key, how='inner')

    # 데이터 타입 확인
    print("flow_df dtypes:")
    print(flow_df[merge_key].dtypes)
    print("sales_df dtypes:")
    print(sales_df[merge_key].dtypes)

    save_file = f"C:/Users/user/Downloads/서울_유동인구_매출_2024_{quarter}.csv"

    if os.path.exists(save_file):
        os.remove(save_file)

    flow_grouped.to_csv(save_file, encoding='utf-8-sig', index=False)
    print("저장 o")

# # 상관계수 및 공분산 계산
# correlation = merged['총_유동인구_수'].corr(merged['당월_매출_금액'])
# covariance = np.cov(merged['총_유동인구_수'], merged['당월_매출_금액'])[0, 1]
#
# print("상관계수:", correlation)
# print("공분산:", covariance)
#
# # 한글 폰트 설정
# plt.rcParams['font.family'] = 'Malgun Gothic'
# plt.rcParams['axes.unicode_minus'] = False
#
# # 산점도 시각화
# plt.figure(figsize=(10, 6))
# plt.scatter(merged['총_유동인구_수'], merged['당월_매출_금액'], alpha=0.6)
# plt.title('유동인구 vs 매출액 (2024년 1분기)')
# plt.xlabel('총 유동인구수')
# plt.ylabel('당월 매출금액')
# plt.grid(True)
# plt.tight_layout()
# plt.show()
#
# # 분석 결과 CSV로 저장
# merged.to_csv("C:/Users/user/Downloads/유동인구_매출_분석결과_2024_1분기.csv", encoding='utf-8-sig')
# print("CSV 저장 완료")
