import pickle

from datasets import Dataset
from sklearn.preprocessing import LabelEncoder
from transformers import (
    BertTokenizer,
    BertForSequenceClassification,
    Trainer,
    TrainingArguments,
)

# 모듈 학습 단어
# intent: 0 - 매출_조회
매출_조회 = [
    "매출액",
    "매출이 궁금해",
    "매출액 알려줘",
    "서울 종로구의 매출이 궁금해",
    "서울 강남구 매출 알려줘",
    "해당 지역의 매출을 보여줘",
    "이 동네 매출 얼마나 돼?",
    "매출 데이터 알려줘",
    "유성구 매출 얼마나 나와?",
    "서울 매출 통계 알려줘",
    "지역 매출 현황 보여줘",
    "상권 매출 정보 보고 싶어",
    "서울 매출 추이 알려줘",
    "여기 매출 정보 줘",
    "구별 매출 비교해줘",
    "이 지역의 매출 현황이 궁금해",
    "업종별 매출액 분포 알려줘",
    "최고 매출 업종은 뭐야?",
    "서울시 평균 매출 데이터 보여줘",
    "여기 상권의 매출 현황 알려줘"
]

# intent: 1 - 유동인구_조회
유동인구_조회 = [
    "서울 유동인구 수는?",
    "서울 인구 수는?",
    "서울 종로구 유동인구 얼마나 돼?",
    "서울 용산구 인구 얼마나 돼?",
    "20대 남자 인구 수 알려줘",
    "50대 여자 유동인구 수 알려줘",
    "연령별 인구 수 보여줘",
    "성별 인구 통계 줘"
    "성별 유동인구 수 알려줘"
    "서울 중구 인구 얼마나 돼?",
    "이 지역 인구 현황 알려줘",
    "최근 유동인구 추이 보여줘",
    "연령대별 유동인구 통계 줘",
    "강북구 유동인구 수 알려줘",
    "성별/연령별 인구 통계 보여줘",
    "여성 인구 수 얼마나 돼?",
    "남성 인구 비율 알려줘",
    "60대 이상 인구 수 알려줘",
    "전체 인구 통계 알려줘",
    "서울 은평구 30대 인구 수 알려줘",
    "연령별 성별 인구 수 보여줘",
    "서울의 유동인구 변화 알려줘",
    "성별 유동 인원 수 얼마나 돼?"
]

# intent: 2 - 위험도
위험도 = [
    "폐업 위험도 높은 지역은?",
    "위험한 상권 알려줘",
    "어디가 위험한 상권이야?",
    "상권 분석 결과 보여줘",
    "위험 지역 분석해줘"
]

# intent: 3 - 청약_정보
청약_정보 = [
    "폐업 위험도 높은 지역은?",
    "위험한 상권 알려줘",
    "어디가 위험한 상권이야?",
    "상권 분석 결과 보여줘",
    "위험 지역 분석해줘"
]

# ✅ 2. 텍스트 전처리
train_sentences = 매출_조회 + 유동인구_조회 + 위험도 + 청약_정보
train_labels = [0]*len(매출_조회) + [1]*len(유동인구_조회) + [2]*len(위험도) + [3]*len(청약_정보)

# ✅ 2. 라벨 인코딩
le = LabelEncoder()
encoded_labels = le.fit_transform(train_labels)
texts = train_sentences

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
