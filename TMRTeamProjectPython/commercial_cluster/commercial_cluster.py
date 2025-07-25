import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import matplotlib

# 한글 폰트 설정 (Windows: 맑은 고딕)
matplotlib.rcParams['font.family'] = 'Malgun Gothic'

# 마이너 경고 제거 (음수 깨짐 방지)
matplotlib.rcParams['axes.unicode_minus'] = False

# 분석할 업종 데이터 불러오기
df = pd.read_csv('C:/Users/admin/Desktop/업종별_병합결과/CS100001_한식음식점.csv')

selected_features = [
    # 점포/경쟁 정보
    '점포_수', '개업_율', '폐업_률', '프랜차이즈_점포_수',

    # 매출 정보 (금액만)
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_20_매출_금액', '연령대_30_매출_금액', '연령대_40_매출_금액',

    # 유동인구
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',

    # 상주/직장인구
    '총_상주인구_수', '총_직장_인구_수',

    # 소득 소비
    '월_평균_소득_금액', '지출_총금액', '음식_지출_총금액',

    # 집객시설
    '지하철_역_수', '대학교_수', '관공서_수'
]

df_selected = df[selected_features].fillna(0)

# 정규화
scaler = StandardScaler()
X = scaler.fit_transform(df_selected)

# 군집 수 결정 (엘보우 예시)
inertia = []
K_range = range(2, 10)
for k in K_range:
    model = KMeans(n_clusters=k, random_state=42)
    model.fit(X)
    inertia.append(model.inertia_)

plt.plot(K_range, inertia, marker='o')
plt.xlabel('k (클러스터 수)')
plt.ylabel('inertia (군집 응집도)')
plt.title('엘보우 그래프')
plt.show()

# 실제 군집 분석
kmeans = KMeans(n_clusters=4, random_state=42)
df['cluster'] = kmeans.fit_predict(X)

# ✅ 결과 저장
df.to_csv('C:/Users/admin/Desktop/업종별_병합결과_클로스터링/CS100001_한식음식점_클러스터링.csv', index=False, encoding='utf-8-sig')

# ✅ 클러스터별 평균 확인
print(df.groupby('cluster')[selected_features].mean())