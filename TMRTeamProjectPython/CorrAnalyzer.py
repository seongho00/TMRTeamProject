import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

results = []

merge_key = ['행정동_코드', '행정동_코드_명']

for quarter in [20241, 20242, 20243, 20244]:
    file_path = f"C:/Users/user/Downloads/서울_유동인구_매출_{quarter}.csv"
    df = pd.read_csv(file_path)

    # 행정동 기준 유동인구 평균 및 매출 합계 계산
    grouped_df = df.groupby(merge_key).agg({
        '총_유동인구_수': 'mean',
        '당월_매출_금액': 'sum'
    }).reset_index()

    grouped_df['기준_년분기_코드'] = quarter

    # 컬럼명 변경
    grouped_df.rename(columns={
        '총_유동인구_수': '총_유동인구_수',
        '당월_매출_금액': '당월_총_매출_금액'
    }, inplace=True)

    # 4. 상관계수 및 공분산 계산
    correlation = grouped_df['총_유동인구_수'].corr(grouped_df['당월_총_매출_금액'])
    covariance = np.cov(grouped_df['총_유동인구_수'], grouped_df['당월_총_매출_금액'])[0, 1]

    print(f"상관계수: {correlation:.4f}")
    print(f"공분산: {covariance:.2f}")

    # 5. 분석결과 저장
    save_path = f"C:/Users/user/Downloads/유동인구_매출_분석결과_{quarter}.csv"
    grouped_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {save_path}")

    # 6. 시각화 (선택)
    plt.figure(figsize=(8, 5))
    plt.scatter(grouped_df['총_유동인구_수'], grouped_df['당월_총_매출_금액'], alpha=0.5)
    plt.title(f"{quarter} 유동인구 vs 매출")
    plt.xlabel("유동인구 수")
    plt.ylabel("당월 총 매출 금액")
    plt.grid(True)
    plt.tight_layout()
    plt.show()
