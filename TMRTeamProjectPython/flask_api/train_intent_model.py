from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.preprocessing import LabelEncoder
from datasets import Dataset
import pickle
from transformers import (
    BertTokenizer,
    BertForSequenceClassification,
    Trainer,
    TrainingArguments,
)


# 모듈 학습 단어
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

# ✅ 2. 라벨 인코딩
le = LabelEncoder()
encoded_labels = le.fit_transform(train_labels)
texts = train_sentences  # 누락되어 있었음!

# ✅ 3. BERT 모델 및 토크나이저 로드 (한국어용 사전학습 모델 사용)
model_name = "klue/bert-base"
tokenizer = BertTokenizer.from_pretrained(model_name)


# ✅ 4. HuggingFace Dataset 생성
data = Dataset.from_dict({"text": texts, "label": encoded_labels})

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True, padding="max_length", max_length=32)

tokenized_data = data.map(tokenize, batched=True)

# ✅ 5. 모델 정의
model = BertForSequenceClassification.from_pretrained(model_name, num_labels=len(le.classes_))


# ✅ 6. Trainer 학습 설정
training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=5,
    per_device_train_batch_size=8,
    logging_dir="./logs",
    logging_steps=10,
    save_strategy="no"
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_data,
)

# ✅ 7. 학습 실행
trainer.train()

# ✅ 8. 모델 및 라벨 인코더 저장
model.save_pretrained("./intent_bert_model")
tokenizer.save_pretrained("./intent_bert_model")

with open("label_encoder.pickle", "wb") as f:
    pickle.dump(le, f)

print("✅ BERT intent 분류 모델 저장 완료")