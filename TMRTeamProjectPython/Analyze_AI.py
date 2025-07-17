import pandas as pd
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# 데이터 불러오기
df = pd.read_csv("trade_area_data.csv")

# 필요 없는 열 제거 (지역ID, 지역명 등)
df = df.drop(columns=["지역ID", "지역명"])

# 입력 (X), 출력 (y) 분리
X = df.drop(columns=["과거3개월매출(만원)"])
y = df["과거3개월매출(만원)"]

# 정규화
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 학습/검증 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# 모델 구성
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation='relu', input_shape=(X_train.shape[1],)),
    tf.keras.layers.Dense(32, activation='relu'),
    tf.keras.layers.Dense(1)  # 회귀이므로 activation 없음
])

model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# 학습
model.fit(X_train, y_train, epochs=100, batch_size=8, validation_split=0.1)

# 평가
loss, mae = model.evaluate(X_test, y_test)
print(f"Test MAE: {mae:.2f}")

# 예측 예시
predicted = model.predict(X_test[:5])
print("예측 결과:", predicted.flatten())
