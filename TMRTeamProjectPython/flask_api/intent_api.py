from flask import Flask, request, jsonify, Response
import json
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pickle
import re
import mecab_ko
import pymysql
from werkzeug.utils import secure_filename
import os, uuid, tempfile, hashlib

# 사진 업로드 저장 디렉토리 (스프링과 동일/공유 경로면 더 좋음)
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "registry-uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 허용 MIME (필요시 application/pdf 추가)
ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/heic"}

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
def analyze_input(user_input, valid_emd_list):
    # 시도 목록 (단일 단어 기준)
    valid_sido = {'대전'}

    # 시군구 목록
    valid_sigungu = {'서구', '유성구', '대덕구', '동구', '중구'}

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

    nouns = extract_nouns_with_age_merge(user_input)
    print("추출된 명사:", nouns)
    gender = None
    age_group = None
    sido = None
    sigungu = None
    emd_nm = None

    for token in nouns:
        # 시도 설정
        if token in valid_sido:
            sido = token
        
        # 시군구 설정
        if token in valid_sigungu:
            sigungu = token
            
        # 성별 설정
        if token in gender_keywords:
            gender = gender_keywords[token]
            
        # 나이대 설정
        if token in age_keywords:
            age_group = age_keywords[token]
            
        # 행정동 설정
        if token in valid_emd_list:
            emd_nm = token  # ✅ 행정동 이름 저장

    return gender, age_group, sido, sigungu, emd_nm


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
valid_emd_list = extract_emd_nm_list()

# ✅ API 라우팅
@app.route("/predict", methods=["GET"])
def predict():
    question = request.args.get("text", "").strip()

    if not question:
        return jsonify({"error": "text 파라미터가 비어있습니다."}), 400

    # 예측
    intent, confidence = predict_intent(question)

    # 기본 응답
    response_data = {
        "intent": str(intent),
        "confidence": float(round(confidence, 4)),
        "message": generate_response(question)
    }

    # intent가 1(유동인구 조회)일 때만 의미 분석 실행
    if intent == 1:
        gender, age_group, sido, sigungu, emd_nm = analyze_input(question, valid_emd_list)
        response_data.update({
            "sido": str(sido),
            "sigungu": str(sigungu),
            "emd_nm": str(emd_nm),
            "gender": str(gender),
            "age_group": str(age_group)
        })

    return Response(
        json.dumps(response_data, ensure_ascii=False),
        content_type="application/json; charset=utf-8"
    )


def _sha1(path, limit=1024*128):
    """파일 앞부분만 읽어 빠른 체크섬(선택)"""
    h = hashlib.sha1()
    with open(path, "rb") as f:
        chunk = f.read(limit)
        h.update(chunk)
    return h.hexdigest()


@app.route("/analyze", methods=["POST"])
def analyze():
    if "files" not in request.files:
        return jsonify(ok=False, message="files 필드가 없습니다."), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify(ok=False, message="업로드된 파일이 없습니다."), 400

    saved = []
    app.logger.info("📥 받은 파일 수: %d", len(files))

    for f in files:
        if not f or f.filename == "":
            continue

        ctype = (f.mimetype or "").lower()
        if ctype not in ALLOWED:
            return jsonify(ok=False, message=f"허용되지 않은 형식: {ctype}"), 415

        base, ext = os.path.splitext(secure_filename(f.filename))
        ext = ext or ".jpg"
        fname = f"{uuid.uuid4()}{ext}"
        path = os.path.join(UPLOAD_DIR, fname)

        # 저장
        f.save(path)

        # 디스크 검증
        exists = os.path.exists(path)
        size_on_disk = os.path.getsize(path) if exists else 0
        head = b""
        with open(path, "rb") as rf:
            head = rf.read(16)  # 매직넘버로 파일 유형도 대략 확인 가능

        # 로그로도 남기기
        app.logger.info("✅ saved: %s (%s) size=%d exists=%s head=%s",
                        path, ctype, size_on_disk, exists, head)

        saved.append({
            "originalName": f.filename,
            "contentType": ctype,
            "storedPath": path,
            "fileName": fname,
            "size_header": getattr(f, "content_length", None),  # 요청 헤더상의 사이즈(없을 수 있음)
            "size_on_disk": size_on_disk,                      # 실제 저장된 크기
            "exists": exists,                                   # 디스크 존재 여부
            "head_magic": head.hex(),                           # 앞 16바이트(매직넘버)
            "sha1_head": _sha1(path)                            # 빠른 체크용 체크섬(선택)
        })

    if not saved:
        return jsonify(ok=False, message="저장된 파일이 없습니다."), 400

    return jsonify(ok=True, count=len(saved), files=saved), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)

