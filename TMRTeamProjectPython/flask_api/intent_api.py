from flask import Flask, request, jsonify, Response
import json
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pickle
import re
import mecab_ko

tagger = mecab_ko.Tagger()
print(tagger.parse("대전에 있는 유성구의 유동인구 알려줘"))

app = Flask(__name__)

# ✅ intent label 복원 (라벨 인코더로)
with open("label_encoder.pickle", "rb") as f:
    label_encoder = pickle.load(f)
intent_labels = list(label_encoder.classes_)

# ✅ HuggingFace BERT 모델 및 토크나이저 로드
MODEL_PATH = "./intent_bert_model"
tokenizer = BertTokenizer.from_pretrained(MODEL_PATH)
model = BertForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval()


# ✅ 예측 함수
def predict_intent(text, threshold=0.1):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=32)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1)[0]
        confidence, predicted_class_id = torch.max(probs, dim=0)

    confidence = confidence.item()
    class_idx = predicted_class_id.item()

    if confidence < threshold:
        return "지원하지 않는 서비스입니다.", confidence

    predicted_label = label_encoder.inverse_transform([class_idx])[0]
    return predicted_label, confidence


def extract_location(text):
    valid_city_map = {
        '대전': ['서구', '유성구', '대덕구', '동구', '중구']
    }
    # 시도 + 시군구 + 읍면동까지 추출
    pattern = r"(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)[\s]*(?:특별시|광역시|도)?[\s]*" \
              r"([가-힣]+[시군구])?[\s]*([가-힣]+[동면읍])?"

    match = re.search(pattern, text)
    if match:
        sido, sigungu, eupmyeondong = match.groups()
        if sigungu and sigungu not in valid_city_map.get(sido, []):
            return "❌ 행정구역 형식에 맞지 않음"  # ❌ 유효하지 않은 조합
        parts = [sido, sigungu, eupmyeondong]
        return " ".join(p for p in parts if p)

    return None


# ✅ 의도 + 지역 기반 응답 생성
def generate_response(user_input):
    intent, confidence = predict_intent(user_input)
    location = extract_location(user_input)

    if intent == 0:
        if location:
            return f"✅ '{location}'의 매출 정보를 조회합니다."
        else:
            return "⚠️ 매출 정보를 조회하려면 지역명을 입력해 주세요."

    elif intent == 1:
        if location:
            return f"📊 '{location}'의 인구 통계를 조회합니다."
        else:
            return "⚠️ 인구 정보를 조회하려면 지역명을 입력해 주세요."

    elif intent == 2:
        return "🚨 폐업 위험도 높은 상권을 분석 중입니다."

    else:
        return "❓ 지원하지 않는 서비스입니다."


# ✅ 명사만 추출하는 함수
def extract_nouns(text):
    parsed = tagger.parse(text)
    lines = parsed.split('\n')
    nouns = []

    for line in lines:
        if line == 'EOS' or line == '':
            continue
        word, feature = line.split('\t')
        pos = feature.split(',')[0]

        if pos in ['NNG', 'NNP']:  # 일반명사 or 고유명사
            nouns.append(word)

    return nouns

# ✅ 의미 분석 함수
def analyze_input(user_input):
    valid_city_map = {
        '대전': ['서구', '유성구', '대덕구', '동구', '중구']
    }

    gender_keywords = {
        "남자": "male", "남성": "male",
        "여자": "female", "여성": "female"
    }

    age_keywords = {
        "10대": "age_10",
        "20대": "age_20",
        "30대": "age_30",
        "40대": "age_40",
        "50대": "age_50",
        "60대": "age_60"
    }

    nouns = extract_nouns(user_input)

    gender = None
    age_group = None
    sido = None
    sigungu = None

    for token in nouns:
        for city in valid_city_map:
            if token.startswith(city):
                sido = city
        if sido and token in valid_city_map[sido]:
            sigungu = token
        if token in gender_keywords:
            gender = gender_keywords[token]
        if token in age_keywords:
            age_group = age_keywords[token]

    return gender, age_group, sido, sigungu

# ✅ API 라우팅
@app.route("/predict", methods=["GET"])
def predict():
    question = request.args.get("text", "").strip()

    if not question:
        return jsonify({"error": "text 파라미터가 비어있습니다."}), 400

    # 예측
    intent, confidence = predict_intent(question)

    # 메세지
    message = generate_response(question)

    # ✅ 성별, 연령, 지역 모두 추출 (MeCab 기반)
    gender, age_group, sido, sigungu = analyze_input(question)


    return Response(
        json.dumps({
            "intent": str(intent),
            "confidence": float(round(confidence, 4)),
            "sido": str(sido),
            "sigungu": str(sigungu),
            "gender": str(gender),
            "age_group": str(age_group),
            "message": str(message)
        }, ensure_ascii=False),
        content_type="application/json; charset=utf-8"
    )



if __name__ == "__main__":
    app.run(port=5000, debug=True)
