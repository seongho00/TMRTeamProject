import tensorflow as tf
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np



# ✅ 1. 학습 데이터 정의 (Intent 분류용)
train_sentences = [
    "대전 유성구 매출 알려줘",
    "2023년 서울 인구 수 보여줘",
    "폐업 위험 높은 지역 알려줘",
    "안녕",
    "상권 위험도 분석해줘",
    "30대 남성 인구 수는?",
    "이 매장의 매출이 궁금해",
    "위험 지역 어디야?",
]

train_labels = [
    0,  # 매출_조회
    1,  # 인구_조회
    2,  # 상권_위험도
    3,  # 기타
    2,
    1,
    0,
    2
]

# ✅ 2. 텍스트 전처리
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
model.save("intent_model.h5")

# ✅ 5. 토크나이저도 저장 (Flask에서 재사용)
import pickle
with open("tokenizer.pickle", "wb") as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)

print("✅ 모델 및 토크나이저 저장 완료")