import glob
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
from sklearn.utils import compute_class_weight
from tqdm import tqdm

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

df_dir = "C:/Users/user/Downloads/seoul_data_merge"

# df_dir 폴더에 있는 모든 데이터 불러오기
csv_files = glob.glob(os.path.join(df_dir, "*.csv"))

train_quarters = ['20231', '20232', '20233', '20234', '20241', '20242', '20243', '20244']
test_quarter = '20251'

df_train = pd.concat([
    pd.read_csv(f) for f in csv_files if any(q in f for q in train_quarters)
], ignore_index=True)

df_test = pd.concat([
    pd.read_csv(f) for f in csv_files if test_quarter in f
], ignore_index=True)

df_train = df_train[[col for col in df_train.columns if '아파트' not in col]]
df_test = df_test[[col for col in df_train.columns if '아파트' not in col]]

# 군집분석
cluster_features = [
    '점포_수', '개업_율', '폐업_률', '프랜차이즈_점포_수',
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_20_매출_금액', '연령대_30_매출_금액', '연령대_40_매출_금액',
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '총_상주인구_수', '총_직장_인구_수',
    '월_평균_소득_금액', '지출_총금액', '음식_지출_총금액'
]

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_train[cluster_features].fillna(0))

kmeans = KMeans(n_clusters=5, random_state=42)
df_train['cluster'] = kmeans.fit_predict(X_scaled)

# 상관분석
correlation_features = []

correlation_features += [
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '연령대_10_유동인구_수', '연령대_20_유동인구_수', '연령대_30_유동인구_수',
    '연령대_40_유동인구_수', '연령대_50_유동인구_수', '연령대_60_이상_유동인구_수',
    '시간대_유동인구_수_00~06', '시간대_유동인구_수_06~11', '시간대_유동인구_수_11~14',
    '시간대_유동인구_수_14~17', '시간대_유동인구_수_17~21', '시간대_유동인구_수_21~24',
    '요일별_유동인구_수_평일', '요일별_유동인구_수_주말'
]

correlation_features += [
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '요일_매출_월요일', '요일_매출_화요일', '요일_매출_수요일', '요일_매출_목요일',
    '요일_매출_금요일', '요일_매출_토요일', '요일_매출_일요일',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_10_매출_금액', '연령대_20_매출_금액', '연령대_30_매출_금액',
    '연령대_40_매출_금액', '연령대_50_매출_금액', '연령대_60_이상_매출_금액'
]

correlation_features += [
    '총_상주인구_수', '남성_상주인구_수', '여성_상주인구_수',
    '연령대_10_상주인구_수', '연령대_20_상주인구_수', '연령대_30_상주인구_수',
    '연령대_40_상주인구_수', '연령대_50_상주인구_수', '연령대_60_이상_상주인구_수',
    '총_가구_수'
]

correlation_features += [
    '월_평균_소득_금액', '지출_총금액',
    '식료품_지출_금액', '의류_신발_지출_금액', '생활용품_지출_금액',
    '의료비_지출_금액', '여가_지출_금액', '문화_지출_금액'
]

correlation_features += [
    '점포_수', '프랜차이즈_점포_수', '개업_점포_수', '폐업_점포_수', '유사_업종_점포_수'
]

correlation_features += [
    '총_직장_인구_수', '남성_직장_인구_수', '여성_직장_인구_수',
    '연령대_10_직장_인구_수', '연령대_20_직장_인구_수', '연령대_30_직장_인구_수',
    '연령대_40_직장_인구_수', '연령대_50_직장_인구_수', '연령대_60_이상_직장_인구_수'
]

correlation_features = [
    col for col in correlation_features
    if '아파트' not in col and not any(x in col for x in ['지하철', '학교', '관공서', '병원', '약국', '은행', '유치원', '학원'])
]

cor_matrix = df_train.corr(numeric_only=True)
cor_target = '당월_매출_금액'
correlations = cor_matrix[[cor_target]].sort_values(by=cor_target, ascending=False)
top_corr_features = correlations.drop(index=cor_target).head(20).index.tolist()

if '폐업_률' in df_train.columns:
    df_train['위험도'] = pd.cut(df_train['폐업_률'], bins=3, labels=[0, 1, 2])
else:
    df_train['위험도'] = np.random.randint(0, 3, size=len(df_train))

X = df_train[top_corr_features + ['cluster']]
y = df_train['위험도']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 가중치 계산
classes = np.unique(y_train)
weights = compute_class_weight(class_weight='balanced', classes=classes, y=y_train)
class_weights_dict = dict(zip(classes, weights))

rf = RandomForestClassifier(
    n_estimators=1,
    warm_start=True,
    random_state=42,
    class_weight=class_weights_dict
)
total_trees = 100
for i in tqdm(range(1, total_trees + 1), desc="진행률", unit="트리"):
    rf.n_estimators = i
    rf.fit(X_train, y_train)

y_pred = rf.predict(X_test)

print(y_train.value_counts())
print(y_pred)
print(classification_report(y_test, y_pred))

# 시각화
importances = pd.Series(rf.feature_importances_, index=X.columns).sort_values(ascending=True)
plt.figure(figsize=(10, 7))
importances.plot(kind='barh')
plt.title('RandomForest 중요도')
plt.tight_layout()
plt.show()
