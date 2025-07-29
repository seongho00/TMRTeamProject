import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_squared_error
import matplotlib.pyplot as plt

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 데이터 불러오기
df = pd.read_csv("C:/Users/user/Downloads/유동인구_매출_분석결과_2024_1분기.csv", encoding='utf-8-sig')

# 사용할 피처(변수) 선택
feature_cols = [
    '당월_매출_금액',
    '총_유동인구_수'
]
X = df[feature_cols]
y = df['당월_매출_금액']

# 학습/테스트 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 선형 회귀 모델 학습
model = LinearRegression()
model.fit(X_train, y_train)

# 예측
y_pred = model.predict(X_test)

# 결과 평가
r2 = r2_score(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)

print("🔍 R² (설명력):", round(r2, 4))
print("📉 MSE (평균제곱오차):", round(mse, 2))

# 회귀계수 출력
print("\n📌 회귀계수:")
for name, coef in zip(feature_cols, model.coef_):
    print(f"{name}: {coef:.2f}")

# 산점도 그래프 (실제 vs 예측)
plt.figure(figsize=(8, 6))
plt.scatter(y_test, y_pred, alpha=0.6)
plt.xlabel('실제 매출액')
plt.ylabel('예측 매출액')
plt.title('실제 vs 예측 매출액')
plt.grid(True)
plt.plot([y.min(), y.max()], [y.min(), y.max()], 'r--')  # 기준선
plt.tight_layout()
plt.show()
