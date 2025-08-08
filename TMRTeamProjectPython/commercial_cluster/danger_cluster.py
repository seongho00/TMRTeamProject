import os

import pandas as pd
from matplotlib import pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# 한글 깨짐 방지
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

file_dir = 'C:/Users/user/Downloads/업종별_병합결과_클로스터링'
save_dir = 'C:/Users/user/Downloads/업종별_위험도_분석'
os.makedirs(save_dir, exist_ok=True)

# 위험도 기준 함수 정의
def get_risk_level(rate):
    if rate >= 0.25:
        return '위험'
    elif rate >= 0.15:
        return '주의'
    else:
        return '양호'

# 시각화 색 매핑
color_map = {
    '양호': 'green',
    '주의': 'orange',
    '위험': 'red'
}

# feature 목록
selected_features = [
    '점포_수', '개업_율', '폐업_률', '프랜차이즈_점포_수',
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_20_매출_금액', '연령대_30_매출_금액', '연령대_40_매출_금액',
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '총_상주인구_수', '총_직장_인구_수',
    '월_평균_소득_금액', '지출_총금액', '음식_지출_총금액',
    '지하철_역_수', '대학교_수', '관공서_수'
]

file_list = os.listdir(file_dir)

for file_name in file_list:
    file_path = os.path.join(file_dir, file_name)

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        print(f"{file_name} 읽기 실패 : {e}")

    # 필수 컬럼이 없으면 건너뜀
    if 'cluster' not in df.columns or '폐업_률' not in df.columns:
        print(f"{file_name} 필수 컬럼 없음, 건너뜀")
        continue

    # 클러스터 평균 폐업률 → 위험도 계산
    cluster_avg = df.groupby('cluster')['폐업_률'].mean().to_dict()
    df['위험도'] = df['cluster'].map(lambda c: get_risk_level(cluster_avg.get(c, 0)))

    # 정규화 + PCA
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(df[selected_features].fillna(0))
    pca = PCA(n_components=2)
    X_pca = pca.fit_transform(X_scaled)
    df['PC1'] = X_pca[:, 0]
    df['PC2'] = X_pca[:, 1]

    # 시각화
    plt.figure(figsize=(8, 6))
    for risk_level in df['위험도'].unique():
        subset = df[df['위험도'] == risk_level]
        plt.scatter(subset['PC1'], subset['PC2'],
                    label=risk_level,
                    alpha=0.7,
                    color=color_map.get(risk_level, 'gray'))
    plt.title(f'PCA 위험도 시각화 - {file_name}')
    plt.xlabel('PC1')
    plt.ylabel('PC2')
    plt.legend()
    plt.grid(True)

    # 이미지 저장
    image_path = os.path.join(save_dir, f"{os.path.splitext(file_name)[0]}_위험도시각화.png")
    plt.savefig(image_path)
    plt.close()

    # CSV 저장
    save_path = os.path.join(save_dir, file_name)
    df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"완료: {file_name} → 위험도 분석 + 시각화 저장")
