import pandas as pd
import pymysql
import numpy as np
import tensorflow as tf
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split

conn = pymysql.connect(
    host="localhost",
    port=3306,
    user="root",
    password="",
    db="TMRTeamProject",
    charset="utf8mb4"
)

qurey = """
        SELECT
            store_count AS storeCount,
            store_count_yoy_change AS storeCountYoyChange,
            store_count_mom_change AS storeCountMomChange,
            foot_traffic AS footTraffic,
            monthly_sales AS monthlySales,
            sales_yoy_change AS salesYoyChange,
            sales_mom_change AS salesMomChange,
            industry
        FROM trade_area
        WHERE industry IS NOT NULL
"""

df = pd.read_sql(qurey, conn)
conn.close()

print(df.all)

X = df[[
    'storeCount',
    'storeCountYoyChange',
    'storeCountMomChange',
    'footTraffic',
    'monthlySales',
    'salesYoyChange',
    'salesMomChange'
]]

# 2. 업종 라벨 인코딩
label_encoder = LabelEncoder()
y = label_encoder.fit_transform(df['industry'])

# 3. 원-핫 인코딩
y_onehot = tf.keras.utils.to_categorical(y)

# 4. 스케일링
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 5. 데이터 분할
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_onehot, test_size=0.2, random_state=42)

# 6. 모델 정의 (Softmax 분류기)
model = tf.keras.Sequential([
    tf.keras.layers.Input(shape=(X_train.shape[1],)),
    tf.keras.layers.Dense(y_onehot.shape[1], activation='softmax')
])

model.compile(optimizer='adam',
              loss='categorical_crossentropy',
              metrics=['accuracy'])

# 7. 학습
model.fit(X_train, y_train, epochs=30, batch_size=16, validation_split=0.2)

# 8. 평가
loss, acc = model.evaluate(X_test, y_test)
print(f"테스트 정확도: {acc:.4f}")

# 9. 예측 예시
sample = np.array([[25, -2.0, -1.0, 1500, 400, -5.0, -3.0]])  # 배달 없음
sample_scaled = scaler.transform(sample)
pred = model.predict(sample_scaled)
predicted_index = np.argmax(pred[0])
predicted_label = label_encoder.inverse_transform([predicted_index])[0]

print(f"예측 업종: {predicted_label}")
print(f"선택 확률: {pred[0]}")
