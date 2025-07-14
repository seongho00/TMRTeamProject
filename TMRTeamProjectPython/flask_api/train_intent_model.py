import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import pickle

# 모듈 학습
# intent: 0 - 매출_조회
매출_조회 = [
    "이 매장의 매출이 궁금해",
    "서울 강남구 매출 알려줘",
    "이번 달 매출 보여줘",
    "2024년 5월 매출 데이터 줘",
    "지역별 매출 비교해줘"
]

# intent: 1 - 인구_조회
인구_조회 = [
    "부산의 인구 수는?",
    "대구 인구 얼마나 돼?",
    "2023년 20대 남자 인구 수 알려줘",
    "연령별 인구 수 보여줘",
    "성별 인구 통계 줘"
]

# intent: 2 - 위험도
위험도 = [
    "폐업 위험도 높은 지역은?",
    "위험한 상권 알려줘",
    "어디가 위험한 상권이야?",
    "상권 분석 결과 보여줘",
    "위험 지역 분석해줘"
]




# ✅ 2. 텍스트 전처리
train_sentences = 매출_조회 + 인구_조회 + 위험도
train_labels = [0]*len(매출_조회) + [1]*len(인구_조회) + [2]*len(위험도)

tokenizer = Tokenizer(num_words=1000, oov_token="<OOV>")
tokenizer.fit_on_texts(train_sentences)

train_sequences = tokenizer.texts_to_sequences(train_sentences)
train_padded = pad_sequences(train_sequences, padding='post')

train_labels = np.array(train_labels)

# ✅ 3. 모델 정의
model = tf.keras.Sequential([
    tf.keras.layers.Embedding(1000, 16),
    tf.keras.layers.GlobalAveragePooling1D(),
    tf.keras.layers.Dense(16, activation='relu'),
    tf.keras.layers.Dense(4, activation='softmax')  # intent 클래스 수
])

model.compile(loss='sparse_categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
model.fit(train_padded, train_labels, epochs=30)

# ✅ 4. 모델 저장
model.save("intent_model.keras")  # 또는
tf.keras.saving.save_model(model, "intent_model.keras")

# ✅ 5. 토크나이저도 저장 (Flask에서 재사용)
with open("tokenizer.pickle", "wb") as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

print("✅ 모델 및 토크나이저 저장 완료")