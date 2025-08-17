from flask import Flask, request, jsonify, Response
import json
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pickle
import mecab_ko
import pymysql
import os, uuid, tempfile, hashlib
import cv2, numpy as np, pytesseract, re
from PIL import Image
from werkzeug.utils import secure_filename

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


# 사진 전처리 및 분석 코드
def _sha1(path, limit=1024 * 128):
    """파일 앞부분만 읽어 빠른 체크섬(선택)"""
    h = hashlib.sha1()
    with open(path, "rb") as f:
        chunk = f.read(limit)
        h.update(chunk)
    return h.hexdigest()


def preprocess_for_ocr(img_bgr: np.ndarray) -> np.ndarray:
    """기본 전처리: 리사이즈 → 그레이 → 잡음제거 → 대비보정 → 이진화"""
    h, w = img_bgr.shape[:2]
    scale = 1400 / max(h, w)
    if scale < 1:
        img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)))
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, 9, 75, 75)  # 잡음 줄이면서 엣지 살리기
    gray = cv2.equalizeHist(gray)  # 대비 향상
    bw = cv2.adaptiveThreshold(gray, 255,
                               cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                               cv2.THRESH_BINARY, 31, 15)
    return bw


def ocr_image(path: str) -> str:
    """이미지 파일 경로 → 전처리 → Tesseract OCR → 텍스트"""
    pil = Image.open(path)  # HEIC도 pillow-heif 등록하면 자동 처리
    pil.load()
    bgr = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)
    pre = preprocess_for_ocr(bgr)
    pil_pre = Image.fromarray(pre)
    text = pytesseract.image_to_string(pil_pre, config=TESS_CONF)
    # 약간의 클린업
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text).strip()
    return text


# 섹션 나누기(표제부/갑구/을구 키워드 기반의 매우 단순한 분리)
SEC_RE = {
    "표제부": re.compile(r"(표제부.*?)(?=갑구|을구|$)", re.S),
    "갑구": re.compile(r"(갑구.*?)(?=표제부|을구|$)", re.S),
    "을구": re.compile(r"(을구.*?)(?=표제부|갑구|$)", re.S),
}


def split_sections(text: str) -> dict:
    secs = {}
    for k, rx in SEC_RE.items():
        m = rx.search(text)
        secs[k] = m.group(1) if m else ""
    return secs


# 을구에서 권리/금액/날짜 아주 기초 추출(정규식 기반 – 서식 차이에 약함)
DATE_RE = r"(\d{4}[./-]\d{1,2}[./-]\d{1,2})"
MONEY_RE = r"([0-9,]+)\s*원"


def parse_eulgu(eul_text: str) -> list:
    """
    예: 순위번호 1 근저당권 ... 접수일 2023-01-01 채권최고액 100,000,000원
    서식이 제각각이라 100% 정확하진 않지만, 기본적인 패턴만 뽑음
    """
    entries = []
    pat = re.compile(
        rf"순위번호\s*(\d+).*?"
        rf"(근저당권|저당권|전세권|임차권|가등기|신탁등기).*?"
        rf"(접수|접수일|원인일자).*?{DATE_RE}.*?"
        rf"(채권최고액|전세금|채권액)?\s*{MONEY_RE}?",
        re.S
    )
    for m in pat.finditer(eul_text):
        entries.append({
            "순위": int(m.group(1)),
            "권리": m.group(2),
            "접수일": re.sub(r"[./]", "-", m.group(4)),
            "금액명": m.group(5) or "",
            "금액": int((m.group(6) or "0").replace(",", "")) if m.group(6) else None
        })
    return entries


@app.route("/analyze", methods=["POST"])
def analyze():
    if "files" not in request.files:
        return jsonify(ok=False, message="files 필드가 없습니다."), 400

    files = request.files.getlist("files")
    if not files:
        return jsonify(ok=False, message="업로드된 파일이 없습니다."), 400

    results_meta = []
    texts = []

    for f in files:
        if not f or f.filename == "":
            continue

        ctype = (f.mimetype or "").lower()
        if ctype not in ALLOWED:
            return jsonify(ok=False, message=f"허용되지 않은 형식: {ctype}"), 415

        # 메타데이터만 보존(저장은 안 함)
        base, ext = os.path.splitext(secure_filename(f.filename))
        ext = ext or ".bin"
        fname = f"{uuid.uuid4()}{ext}"

        # 바이트를 메모리로 읽음
        data = f.read()
        if not data:
            continue

        try:
            if ctype == "application/pdf":
                txt = ocr_pdf_bytes(data)
            else:
                txt = ocr_image_bytes(data, ctype)
        except Exception as e:
            txt = f"[OCR 실패: {e}]"

        results_meta.append({
            "originalName": f.filename,
            "contentType": ctype,
            "fileName": fname,     # 실제 저장은 안 하지만 추적용으로 응답
            "size": len(data),
        })
        texts.append(txt)

    if not results_meta:
        return jsonify(ok=False, message="처리 가능한 파일이 없습니다."), 400

    full_text = "\n\n---PAGEBREAK---\n\n".join(texts)
    secs = split_sections(full_text)
    eul_entries = parse_eulgu(secs.get("을구", ""))

    return jsonify(
        ok=True,
        count=len(results_meta),
        files=results_meta,                 # storedPath 제거됨 (디스크 저장 안 함)
        sections_detected=[k for k, v in secs.items() if v],
        textPreview=full_text[:2000],
        parsed={"을구_entries": eul_entries}
    ), 200


if __name__ == "__main__":
    app.run(port=5000, debug=True)
