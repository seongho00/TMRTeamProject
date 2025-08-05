import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.preprocessing import MinMaxScaler

# ✅ 클러스터링된 데이터 불러오기
df = pd.read_csv('C:/Users/admin/Desktop/업종별_병합결과_클로스터링/CS100001_한식음식점_클러스터링.csv')

# ✅ 사용한 피처 목록 (클러스터링에 쓰인 변수)
features = [
    '점포_수', '개업_율', '폐업_률', '프랜차이즈_점포_수',
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_20_매출_금액', '연령대_30_매출_금액', '연령대_40_매출_금액',
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '총_상주인구_수', '총_직장_인구_수',
    '월_평균_소득_금액', '지출_총금액', '음식_지출_총금액',
    '지하철_역_수', '대학교_수', '관공서_수'
]

# ✅ 결측치 처리
df_selected = df[features + ['cluster']].fillna(0)

# ✅ 클러스터별 평균 계산
cluster_means = df_selected.groupby('cluster')[features].mean()

# ✅ 정규화 (0~1)
scaler = MinMaxScaler()
scaled_means = scaler.fit_transform(cluster_means)
scaled_df = pd.DataFrame(scaled_means, columns=features, index=cluster_means.index)

# ✅ Radar Chart 그리기
def draw_radar_chart(df, title='Radar Chart (Clusters)'):
    labels = df.columns
    num_vars = len(labels)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]  # 원형 연결용

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))

    for idx, row in df.iterrows():
        values = row.tolist()
        values += values[:1]  # 원형 연결용
        ax.plot(angles, values, label=f'Cluster {idx}', linewidth=2)
        ax.fill(angles, values, alpha=0.1)

    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)

    ax.set_thetagrids(np.degrees(angles[:-1]), labels, fontsize=9)
    ax.set_title(title, y=1.1, fontsize=14)
    ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.1))
    plt.tight_layout()
    plt.show()

draw_radar_chart(scaled_df)
