from flask import Flask, request, jsonify, Response
import json
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pickle
import re
import mecab_ko
import pymysql
import pymysql.cursors


# ✅ 예측 함수
def predict_intent(text, threshold=0.1):
    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=32)

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        probs = torch.nn.functional.softmax(logits, dim=1)[0]
        confidence, predicted_class_id = torch.max(probs, dim=0)

    confidence = confidence.item()
    class_idx = int(predicted_class_id.item())

    if confidence < threshold:
        return "지원하지 않는 서비스입니다.", confidence

    return class_idx, confidence


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


# 앱 시작 시 한 번만 실행 (DB에서 행정동 데이터 가져오기)
def extract_emd_nm_list():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        db='TMRTeamProject',
        charset='utf8'
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT DISTINCT emd_nm FROM admin_dong")
            result = cursor.fetchall()
            if result:
                return [row[0] for row in result]
            else:
                return []  # ✅ 빈 리스트라도 리턴
    except Exception as e:
        print("❌ emd_nm 리스트 로딩 실패:", e)
        return []  # ✅ 예외 발생 시에도 빈 리스트
    finally:
        conn.close()


# 앱 시작 시 한 번만 실행 (DB에서 업종 데이터 가져오기)
def extract_upjong_code_map():
    conn = pymysql.connect(
        host='localhost',
        user='root',
        password='',
        db='TMRTeamProject',
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT DISTINCT upjong_cd, upjong_nm
                FROM upjong_code
                WHERE upjong_cd IS NOT NULL AND upjong_nm IS NOT NULL
                ORDER BY upjong_nm
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            name_to_code = {r['upjong_nm']: r['upjong_cd'] for r in rows}
            return name_to_code
    except Exception as e:
        print("❌ 업종 코드 로딩 실패:", e)
        return {}
    finally:
        conn.close()


# ✅ 의미 분석 함수
def analyze_input(user_input, intent, valid_emd_list):
    tokens = extract_nouns_with_age_merge(user_input)
    print("추출된 명사:", tokens)

    entities = {
        "sido": None,
        "sigungu": None,
        "emd_nm": None,
        "gender": None,
        "age_group": None,
        "upjong_cd": None,
        "raw_upjong": None,  # 매칭 안 되면 원문 보관
    }

    for t in tokens:
        # 시/도
        if t in valid_sido:
            entities["sido"] = t
        # 시/군/구
        if t in valid_sigungu:
            entities["sigungu"] = t
        # 행정동
        if t in valid_emd_list:
            entities["emd_nm"] = t
        # 성별
        if t in gender_keywords:
            entities["gender"] = gender_keywords[t]
        # 연령
        if t in age_keywords:
            entities["age_group"] = age_keywords[t]
        # 업종
        if t in upjong_keywords:
            entities["upjong_cd"] = upjong_keywords[t]
            entities["raw_upjong"] = t
        else:
            # 매칭 안 되어도 업종 단어 같으면 원문만 기록(간단 예시)
            if t in ("카페","편의점","분식","패스트푸드","의류"):
                entities["raw_upjong"] = t

    # 지역 최소 단위 판정(하나라도 있으면 OK)
    has_region = bool(entities["emd_nm"] or entities["sigungu"] or entities["sido"])

    # 누락 항목 계산
    required = INTENT_REQUIRED.get(intent, {"need": [], "optional": []})
    missing = []

    if "sido_or_sigungu_or_emd" in required["need"] and not has_region:
        missing.append("region")  # 지역(시/구/동 중 하나)

    # 다른 의무 파라미터가 필요하면 여기에 조건 추가(예: intent별 필수 성별 등)

    return entities, missing


# 숫자 포함 분석
def extract_nouns_with_age_merge(text):
    parsed = tagger.parse(text)
    lines = parsed.split('\n')

    result = []
    i = 0
    while i < len(lines) - 1:  # 마지막 'EOS' 제외
        line = lines[i]
        if line == '' or line == 'EOS':
            i += 1
            continue

        word, feature = line.split('\t')
        features = feature.split(',')

        # 현재 품사
        current_tag = features[0]

        # 숫자 + 대 조합이면 병합
        if current_tag == 'SN' and i + 1 < len(lines):
            next_line = lines[i + 1]
            if '\t' not in next_line:
                i += 1
                continue
            next_word, next_feature = next_line.split('\t')
            next_tag = next_feature.split(',')[0]
            if next_tag == 'NNBC' and next_word == '대':
                result.append(word + next_word)  # 예: "20대"
                i += 2
                continue

        # 명사류만 필터링 (지명/일반명사 등)
        if current_tag in ['NNG', 'NNP']:
            result.append(word)

        i += 1

    return result


# 서버 시작
tagger = mecab_ko.Tagger()

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

# 앱 전체에서 사용할 전역 리스트
valid_sido = {'서울'}

# 시군구 목록
valid_sigungu = {
    '종로구', '중구', '용산구', '성동구', '광진구', '동대문구', '중랑구',
    '성북구', '강북구', '도봉구', '노원구', '은평구', '서대문구', '마포구',
    '양천구', '강서구', '구로구', '금천구', '영등포구', '동작구', '관악구',
    '서초구', '강남구', '송파구', '강동구'
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

valid_emd_list = extract_emd_nm_list()
upjong_keywords = extract_upjong_code_map()

# 의도별 요구 파라미터 정의
# intent: 0=매출, 1=유동인구, 2=위험도, 3=청약(예시)
INTENT_REQUIRED = {
    0: {"need": ["sido_or_sigungu_or_emd", "upjong_cd"], "optional": []},  # 매출 조회: 지역은 최소 1단계, 업종은 선택
    1: {"need": ["sido_or_sigungu_or_emd"], "optional": ["gender", "age_group"]},  # 유동인구: 지역 필수, 성별/연령 선택
    2: {"need": ["sido_or_sigungu_or_emd"], "optional": ["upjong_cd"]},  # 위험도: 지역 필수
    3: {"need": ["sido_or_sigungu_or_emd"], "optional": []},  # 청약: 지역 필수(필요에 맞게 수정)
}


# ✅ API 라우팅
@app.route("/predict", methods=["GET"])
def predict():
    question = request.args.get("text", "").strip()

    if not question:
        return jsonify({"error": "text 파라미터가 비어있습니다."}), 400

    # 예측
    intent_id, confidence = predict_intent(question)

    # 2) 파라미터 분석
    entities, missing = analyze_input(question, intent_id, valid_emd_list)

    # 3) 누락 안내
    if missing:
        parts = []
        if "region" in missing: parts.append("지역(시/구/동)")
        if "upjong_cd" in missing:
            hint = f" (인식: {entities['raw_upjong']})" if entities.get("raw_upjong") else " (예: 카페, 편의점)"
            parts.append("업종" + hint)
        return jsonify({
            "intent": intent_id,
            "confidence": round(confidence, 4),
            "need_more": missing,
            "entities": entities,
            "message": " / ".join(parts) + " 정보를 알려주세요."
        }), 200

    if intent_id == 0:  # 매출
        return jsonify({
            "intent": 0,
            "confidence": round(confidence, 4),
            "entities": entities,   # ← 지역, 업종, 성별, 연령 등 전체 전달
            "data": "...매출조회결과..."
        }), 200

    elif intent_id == 1:  # 유동인구
        return jsonify({
            "intent": 1,
            "confidence": round(confidence, 4),
            "entities": entities,   # ← 지역, 업종, 성별, 연령 등 전체 전달
            "data": "...매출조회결과..."
        }), 200

    elif intent_id == 2:  # 위험도
        return jsonify({
            "intent": 2,
            "confidence": round(confidence, 4),
            "entities": entities,   # ← 지역, 업종, 성별, 연령 등 전체 전달
            "data": "...매출조회결과..."
        }), 200

    else:  # intent_id == 3 등
        return jsonify({
            "intent": int(intent_id),
            "confidence": round(confidence, 4),
            "entities": entities,   # ← 지역, 업종, 성별, 연령 등 전체 전달
            "data": "...매출조회결과..."
        }), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
