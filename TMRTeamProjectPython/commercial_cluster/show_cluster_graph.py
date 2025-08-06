import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# 한글 깨짐 방지
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

# ✅ 클러스터링된 결과 불러오기
file_path = 'C:/Users/user/Downloads/업종별_병합결과_클로스터링/CS100001_한식음식점_클러스터링.csv'
df = pd.read_csv(file_path, encoding='utf-8')

# ✅ 사용할 feature만 추출 (cluster 컬럼 제외)
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

# ✅ 정규화
X = df[selected_features].fillna(0)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ✅ PCA 변환
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

# ✅ 시각화
plt.figure(figsize=(8, 6))
plt.scatter(X_pca[:, 0], X_pca[:, 1], c=df['cluster'], cmap='tab10', alpha=0.7)
plt.title('PCA 시각화 (이미 클러스터링된 결과)')
plt.xlabel('PC1')
plt.ylabel('PC2')
plt.colorbar(label='클러스터 번호')
plt.grid(True)
plt.show()
