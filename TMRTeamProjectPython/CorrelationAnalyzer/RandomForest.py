import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 불러오기
df = pd.read_csv("C:/Users/user/Downloads/서울_데이터_병합_20244.csv", encoding='utf-8')

# 아파트 컬럼 제거
df = df[[col for col in df.columns if '아파트' not in col]]

# 예측 대상
target_col = '당월_매출_금액'

# 예측에 사용할 feature
features = [
    '점포_수', '개업_점포_수', '폐업_점포_수', '프랜차이즈_점포_수', '유사_업종_점포_수',
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '총_직장_인구_수', '총_상주인구_수',
    '월_평균_소득_금액', '지출_총금액', '음식_지출_총금액'
]

# 결측치 처리
df = df[features + [target_col]].dropna()

X = df[features]
y = df[target_col]

# 표준화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 학습/테스트 분할
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# 랜덤포레스트 회귀 모델
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 예측
y_pred = model.predict(X_test)

# 평가 지표
print("RMSE:", np.sqrt(mean_squared_error(y_test, y_pred)))
print("R²:", r2_score(y_test, y_pred))

result_df = pd.DataFrame({
    '실제값': y_test,
    '예측값': y_pred
})
result_df.to_csv("C:/Users/user/Downloads/매출_예측_결과.csv", index=False, encoding='utf-8-sig')

# 중요도 시각화
importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=True)
plt.figure(figsize=(10, 7))
importances.plot(kind='barh')
plt.title('매출 예측 변수 중요도')
plt.tight_layout()
plt.show()

# 매출 예측??
plt.figure(figsize=(10, 5))
plt.plot(y_test.values[:50], label='실제값')
plt.plot(y_pred[:50], label='예측값')
plt.legend()
plt.title("실제 매출 vs 예측 매출")
plt.xlabel("샘플")
plt.ylabel("당월 매출 금액")
plt.tight_layout()
plt.show()

# 원본 df에서 테스트셋에 해당하는 index 정보 가져오기
test_index = X_test.index
df_test = df.loc[test_index, ['행정동_코드', '행정동_코드_명']].copy()

# 예측값과 실제값 DataFrame 구성
df_test['예측_매출'] = y_pred
df_test['실제_매출'] = y_test.values

# 저장
df_test.to_csv("C:/Users/user/Downloads/지도용_예측결과.csv", index=False, encoding='utf-8-sig')
print("지도용 예측 결과 저장 완료")
