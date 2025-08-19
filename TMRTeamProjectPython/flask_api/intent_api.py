from collections import deque
from contextlib import nullcontext

from flask import Flask, request, jsonify, Response
import json
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pickle
import mecab_ko
import pymysql
import io, os, uuid, tempfile
import cv2, numpy as np, pytesseract, re
from PIL import Image
from werkzeug.utils import secure_filename
from pytesseract import Output
import re, time, random, hashlib
from collections import deque
from playwright.sync_api import sync_playwright, Page


# HEIC 지원 (설치되어 있으면 자동 등록)
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

# 크롤링 관련 import
from typing import Any, Dict, List, Optional, Tuple
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout



# 사진 업로드 저장 디렉토리 (스프링과 동일/공유 경로면 더 좋음)
UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "registry-uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# tesseract 엔진 경로 (Doker로 팀플로 전환 예정)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
os.environ["TESSDATA_PREFIX"] = r"C:\Program Files\Tesseract-OCR\tessdata"

# 공통 OCR 설정
LANG_MAIN = "kor"

# 허용 MIME (필요시 application/pdf 추가)
ALLOWED = {"image/jpeg", "image/png", "image/webp", "image/heic"}


print(pytesseract.get_tesseract_version())
print(pytesseract.get_languages(config=f"-l {LANG_MAIN}"))


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


def _cleanup_text(text: str) -> str:
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


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


# 전처리 파이프라인
def build_conf(psm=6, lang=LANG_MAIN):
    # 문서형 레이아웃 기본값
    return f'-l {lang} --oem 3 --psm {psm} --dpi 300 -c preserve_interword_spaces=1'

# --------- (1) 자동 방향 보정 ---------
def auto_orient(pil: Image.Image) -> Image.Image:
    try:
        osd = pytesseract.image_to_osd(pil, config=f'--oem 3 --psm 0 -l {LANG_MAIN}')
        m = re.search(r"Rotate:\s+(\d+)", osd)
        deg = int(m.group(1)) if m else 0
        if deg in (90, 180, 270):
            pil = pil.rotate(-deg, expand=True)
    except Exception:
        pass
    return pil

# --------- (2) 데스큐 + CLAHE(부드러운 그레이 후보) ---------
def deskew(gray: np.ndarray) -> np.ndarray:
    bw = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(bw > 0))
    if coords.size == 0:
        return gray
    angle = cv2.minAreaRect(coords)[-1]
    angle = -(90 + angle) if angle < -45 else -angle
    h, w = gray.shape[:2]
    M = cv2.getRotationMatrix2D((w/2, h/2), angle, 1.0)
    return cv2.warpAffine(gray, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)

def enhance_gray(pil: Image.Image, target_long=2000) -> np.ndarray:
    rgb = np.array(pil.convert("RGB"))
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    h, w = bgr.shape[:2]
    scale = target_long / max(h, w)
    if scale > 1.0:  # 저해상도만 업스케일
        bgr = cv2.resize(bgr, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    gray = clahe.apply(gray)
    gray = deskew(gray)
    return gray

# --------- (3) 너가 가진 크롭/강이진 그대로 사용 ---------
def crop_document(bgr: np.ndarray) -> np.ndarray:
    h, w = bgr.shape[:2]
    y1, y2 = int(0.05*h), int(0.95*h)
    x1, x2 = int(0.06*w), int(0.94*w)
    bgr = bgr[y1:y2, x1:x2].copy()
    try:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 60, 180)
        cnts, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if cnts:
            c = max(cnts, key=cv2.contourArea)
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02*peri, True)
            if len(approx) == 4:
                pts = approx.reshape(4,2).astype(np.float32)
                s = pts.sum(axis=1); diff = np.diff(pts, axis=1)
                rect = np.array([pts[np.argmin(s)], pts[np.argmin(diff)],
                                 pts[np.argmax(s)], pts[np.argmax(diff)]], dtype=np.float32)
                (tl,tr,br,bl) = rect
                W = int(max(np.linalg.norm(br-bl), np.linalg.norm(tr-tl)))
                H = int(max(np.linalg.norm(tr-br), np.linalg.norm(tl-bl)))
                M = cv2.getPerspectiveTransform(rect, np.array([[0,0],[W,0],[W,H],[0,H]], np.float32))
                bgr = cv2.warpPerspective(bgr, M, (W,H))
    except Exception:
        pass
    return bgr

def preprocess_doc(bgr: np.ndarray, upscale_to=2000) -> np.ndarray:
    h, w = bgr.shape[:2]
    scale = max(1.0, upscale_to / max(h, w))
    bgr = cv2.resize(bgr, (int(w*scale), int(h*scale)), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
    bg = cv2.medianBlur(gray, 31)
    norm = cv2.divide(gray, bg, scale=255)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    norm = clahe.apply(norm)
    _, bw = cv2.threshold(norm, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    bw = cv2.medianBlur(bw, 3)
    bw = cv2.morphologyEx(bw, cv2.MORPH_CLOSE, np.ones((2,2), np.uint8), iterations=1)
    return bw

# --------- (4) Tesseract 실행 + 점수화 ---------
def _run_tess(pil_img: Image.Image, psm: int):
    conf = build_conf(psm=psm)
    data = pytesseract.image_to_data(pil_img, config=conf, output_type=Output.DICT)
    words = [w for w in data["text"] if w.strip()]
    confs = [int(c) for c in data["conf"] if c not in ("-1", "-0.0")]
    avg = sum(confs)/len(confs) if confs else 0
    return " ".join(words), avg

def run_ocr(gray: np.ndarray, extra_candidates=None) -> str:
    cands = [gray]
    # 약이진 후보 추가
    thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 31, 15)
    cands.append(thr)
    # 강이진(있으면)도 후보로
    if extra_candidates:
        cands.extend(extra_candidates)

    best_txt, best_score = "", -1.0
    for img in cands:
        pil = Image.fromarray(img)
        for psm in (6, 4, 11, 3):  # 문서(6)→컬럼(4)→스파스(11)→자동(3)
            try:
                txt, avg = _run_tess(pil, psm)
            except Exception:
                continue
            # 한글/전체 길이로 가중치 주기
            score = (avg or 0) + 0.2 * len(re.findall(r"[가-힣]", txt))
            if score > best_score:
                best_score, best_txt = score, txt
    return _cleanup_text(best_txt)

def ocr_image_bytes(data: bytes) -> str:
    # 1) 로드 + 자동 회전
    pil = Image.open(io.BytesIO(data)); pil.load()
    pil = auto_orient(pil)

    # 2) 문서 크롭(가능하면)
    try:
        bgr = cv2.cvtColor(np.array(pil.convert("RGB")), cv2.COLOR_RGB2BGR)
        bgr = crop_document(bgr)
        pil = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    except Exception:
        pass

    # 3) 부드러운 그레이 후보
    gray = enhance_gray(pil, target_long=2000)

    # 4) 강이진 후보 (preprocess_doc)
    extra = []
    try:
        bgr_for_bw = cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
        bw = preprocess_doc(bgr_for_bw)
        extra.append(bw)
    except Exception:
        pass

    # 5) 여러 PSM/후보 조합 → best pick
    return run_ocr(gray, extra_candidates=extra)



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
            txt = ocr_image_bytes(data)
        except Exception as e:
            txt = f"[OCR 실패: {e}]"

        results_meta.append({
            "originalName": f.filename,
            "contentType": ctype,
            "fileName": fname,  # 실제 저장은 안 하지만 추적용으로 응답
            "size": len(data),
        })
        texts.append(txt)

    if not results_meta:
        return jsonify(ok=False, message="처리 가능한 파일이 없습니다."), 400

    full_text = "\n\n---PAGEBREAK---\n\n".join(texts)
    secs = split_sections(full_text)
    # eul_entries = parse_eulgu(secs.get("을구", ""))

    return jsonify(
        ok=True,
        count=len(results_meta),
        files=results_meta,  # storedPath 제거됨 (디스크 저장 안 함)
        sections_detected=[k for k, v in secs.items() if v],
        textPreview=full_text[:2000],
        textFull=full_text,  # ⬅️ 전체 OCR 텍스트 추가
        # parsed={"을구_entries": eul_entries}
    ), 200


# 좌표를 통한 네이버 부동산 실시간 크롤링
# --- Playwright 설정 ---
USER_DATA_DIR = "./.chrome-profile"   # 쿠키/지문 유지
HEADLESS = False                      # 먼저 창 띄워서 확인 후 True로 전환 가능
LIST_SEL_CANDS = [
    "div.item_list.item_list--article",
    "div.item_list--article",
    "div.article_list",  # 예비
]
API_SOFT_WAIT_MS = 1200          # 800~1500 권장 (너무 느리면 900로)
MAX_CLICK = 20                   # 클릭할 카드 수 상한

def _pick_scroll_box(page) -> str:
    # scrollHeight > clientHeight 인 첫 요소 선택
    page.wait_for_selector(", ".join(LIST_SEL_CANDS), timeout=8000)
    for sel in LIST_SEL_CANDS:
        try:
            ok = page.evaluate("""(s) => {
                const el = document.querySelector(s);
                if (!el) return false;
                return el.scrollHeight > el.clientHeight;
            }""", sel)
            if ok:
                return sel
        except:
            pass
    return LIST_SEL_CANDS[0]

def scroll_list_to_bottom(page, pause_ms=700, max_stall=2):
    sel = _pick_scroll_box(page)
    stall = 0
    last_h = -1

    # 컨테이너에 포커스(키보드 스크롤 백업용)
    try:
        page.locator(sel).click(position={"x":10,"y":10}, timeout=1000)
    except:
        pass

    for _ in range(60):  # 충분한 횟수 시도
        try:
            h = page.evaluate("""(s) => {
                const el = document.querySelector(s);
                if (!el) return 0;
                el.scrollTop = el.scrollHeight;
                return el.scrollHeight;
            }""", sel)
        except:
            # 리렌더 됐을 때 다시 고르기
            sel = _pick_scroll_box(page)
            h = page.evaluate("(s) => document.querySelector(s)?.scrollHeight || 0", sel)

        page.wait_for_timeout(pause_ms)

        if h == last_h:
            stall += 1
            if stall >= max_stall:
                break
        else:
            stall = 0
            last_h = h

    # 스크롤 후 카드 수집
    return page.query_selector_all("div.item, div.item_list--article div.item")

def get_env_proxy():
    for k in ("HTTPS_PROXY","https_proxy","HTTP_PROXY","http_proxy"):
        v = os.environ.get(k)
        if v: return {"server": v}
    return None

def _launch_ctx(p):
    proxy_cfg = get_env_proxy()
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        channel="chrome",
        headless=HEADLESS,
        locale="ko-KR",
        viewport={"width": 1280, "height": 860},
        proxy=proxy_cfg,
        ignore_https_errors=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run","--no-default-browser-check",
            "--disable-dev-shm-use","--no-sandbox",
        ],
    )
    # 약식 스텔스
    ctx.add_init_script("""
      Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
      Object.defineProperty(navigator, 'language', {get: () => 'ko-KR'});
      Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR','ko','en-US','en']});
      window.chrome = window.chrome || { runtime: {} };
    """)
    ctx.set_extra_http_headers({"Accept-Language":"ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"})
    return ctx

def _goto_offices(page, lat: float, lng: float):
    root = "https://new.land.naver.com"
    path = f"/offices?ms={lat},{lng},17&a=SG&e=RETAIL"
    page.goto(root, wait_until="domcontentloaded", timeout=30000)
    try:
        page.evaluate("href => { location.href = href }", path)
        page.wait_for_url("**/offices**", timeout=20000)
        return
    except PwTimeout:
        pass
    page.goto(root + path, referer=root, wait_until="domcontentloaded", timeout=30000)
    page.wait_for_url("**/offices**", timeout=20000)


DETAIL_PATTERNS = [
    re.compile(r"https://new\.land\.naver\.com/api/.*/articles/\d+"),
    re.compile(r"https://new\.land\.naver\.com/api/.*/article/\d+"),
    re.compile(r"https://new\.land\.naver\.com/api/.*/detail"),
]

def _soft_wait_detail(page: Page, q: deque, prev_len: int, wait_ms: int) -> Optional[Dict[str, Any]]:
    deadline = time.time() + wait_ms / 1000.0
    while time.time() < deadline:
        if len(q) > prev_len:
            return q[-1]  # 가장 최근 도착분
        page.wait_for_timeout(40)  # 짧게 양보
    return None

def _is_api(url: str) -> bool:
    return "https://new.land.naver.com/api/" in url

def _is_detail(url: str) -> bool:
    return _is_api(url) and any(p.search(url) for p in DETAIL_PATTERNS)

def crawl_viewport(lat: float, lng: float,
                   radius_m: int = 800,
                   category: str = "offices",
                   filters: Optional[Dict[str, Any]] = None,
                   limit_detail_fetch: Optional[int] = 60) -> Dict[str, Any]:

    with sync_playwright() as p:
        ctx = _launch_ctx(p)
        page = ctx.new_page()

        detail_hits: List[Dict[str, Any]] = []

        # 디테일 응답 큐 (on_resp가 여기로 push)
        api_detail_queue: deque = deque()

        def on_resp(resp):
            url = resp.url
            if _is_detail(url):
                try:
                    data = resp.json()
                except Exception:
                    data = None
                api_detail_queue.append({"url": url, "status": resp.status, "data": data})

        page.on("response", on_resp)

        # 1) /offices 진입 & 목록 로드
        _goto_offices(page, lat, lng)
        page.wait_for_timeout(800)
        scroll_list_to_bottom(page, pause_ms=700, max_stall=2)

        # 2) 카드 목록 확보
        page.wait_for_selector(
            "div.item_list--article div.item, div.item_list.item_list--article div.item",
            timeout=6000
        )
        cards = page.query_selector_all(
            "div.item_list--article div.item, div.item_list.item_list--article div.item"
        )

        # 3) 클릭 → (짧게) API 소프트 대기 → DOM 파싱(항상)
        for c in cards[len(cards)]:
            if limit_detail_fetch and len(detail_hits) >= int(limit_detail_fetch):
                break

            try:
                before_len = len(api_detail_queue)
                c.scroll_into_view_if_needed()
                c.click()
            except Exception:
                continue

            # API는 최대 1.2초만 대기 (없어도 통과)
            hit = _soft_wait_detail(page, api_detail_queue, before_len, API_SOFT_WAIT_MS)

            # 디테일 패널 DOM 파싱 (항상 시도)
            page.wait_for_timeout(200)  # 패널 렌더 여유
            try:
                dom_data = scrape_detail_panel(page)   # 또는 scrape_detail_panel_raw(page)
            except Exception:
                dom_data = {}

            detail_hits.append({
                "url":    (hit["url"] if hit else None),
                "status": (hit["status"] if hit else None),
                "json":   (hit["data"] if hit else None),
                "dom":    dom_data,
            })

            # 내부 추가 XHR 시간을 아주 살짝 부여
            page.wait_for_timeout(120 + int(random.random() * 120))

        # 정리
        page.off("response", on_resp)
        ctx.close()

        limit = int(limit_detail_fetch or len(detail_hits))
        return {
            "ok": True,
            "meta": {
                "lat": lat, "lng": lng,
                "category": category,
                "limit_detail_fetch": limit,
                "count_detail": len(detail_hits),
                "source": "playwright_softwait(dom+api)",
            },
            "items": detail_hits[:limit],   # 각 item = {"json":..., "dom":...}
        }

from playwright.sync_api import Page, Locator, TimeoutError as PWTimeout
import re

def wait_for_element(page: Page, selector: str, timeout: int = 6000) -> Locator:
    loc = page.locator(selector)
    loc.wait_for(state="visible", timeout=timeout)
    return loc

def wait_for_elements(page: Page, selector: str, min_count: int = 1, timeout: int = 6000):
    page.wait_for_selector(selector, state="attached", timeout=timeout)
    loc = page.locator(selector)
    # 개수 만족까지 폴링
    with page.expect_event("load", timeout=200) if False else nullcontext():  # no-op
        end = page.context._impl_obj._loop.time() + (timeout / 1000)
        while True:
            if loc.count() >= min_count:
                break
            if page.context._impl_obj._loop.time() > end:
                raise PWTimeout(f"Timeout waiting for {min_count}+ elements: {selector}")
    return [loc.nth(i) for i in range(loc.count())]

def wait_for_child_element(parent: Locator, selector: str, timeout: int = 6000) -> Locator:
    child = parent.locator(selector)
    child.wait_for(state="visible", timeout=timeout)
    return child

def text_or_none(loc: Locator, timeout: int = 3000) -> Optional[str]:
    try:
        return loc.inner_text(timeout=timeout).strip()
    except Exception:
        return None

def get_by_header(page: Page, header_text: str) -> Optional[str]:
    """
    <tr class="info_table_item">
      <th>관리비</th><td>…</td>
    </tr>
    같은 구조에서 헤더 텍스트로 값을 뽑아옴
    """
    row = page.locator(
        "tr.info_table_item",
        has=page.locator("th", has_text=header_text)
    ).first

    if row.count() == 0:
        return None

    return text_or_none(row.locator("td").first)  # text_or_none: Optional[str] 반환

def parse_deposit_monthly(price_value: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    if not price_value or "/" not in price_value:
        return None, None
    a, b = price_value.split("/", 1)
    clean = lambda s: int("".join(ch for ch in s if ch.isdigit())) if any(ch.isdigit() for ch in s) else None
    return clean(a), clean(b)

def scrape_detail_panel(page: Page) -> dict:
    detail = {}

    # 가격 박스
    price_box = wait_for_element(page, "div.info_article_price")
    detail["price_type"]  = text_or_none(price_box.locator(".type"))   # 예: "월세"
    detail["price_value"] = text_or_none(price_box.locator(".price"))  # 예: "4,000/230"

    dep, mon = parse_deposit_monthly(detail["price_value"])
    detail["deposit"] = dep
    detail["monthly"] = mon

    # 상세 테이블(헤더 기반 추출)
    # 페이지마다 라벨이 약간 다를 수 있어, 필요한 것만 골라 호출하면 됨
    candidates = {
        "관리비": ["관리비"],
        "전용면적": ["전용면적", "전용"],
        "공급면적": ["공급면적", "공급"],
        "층": ["층", "층수"],
        "입주가능일": ["입주가능일", "입주일"],
        "주차": ["주차"],
        "난방": ["난방"],
        "용도": ["용도", "주용도"],
        "사용승인일": ["사용승인일", "준공일", "사용승인"],
        "화장실 수": ["화장실 수"],
    }


    for key, labels in candidates.items():
        val = None
        for lbl in labels:
            val = get_by_header(page, lbl)
            if val: break
        detail[key] = val

    # 중개업소(있을 경우)
    broker_box = page.locator("div.broker_info, div.article_broker_info").first
    if broker_box.count() > 0:
        detail["broker_name"]    = text_or_none(broker_box.locator(".name, .broker_name"))
        detail["broker_ceo"]     = text_or_none(broker_box.locator(".ceo, .broker_ceo"))
        detail["broker_address"] = text_or_none(broker_box.locator(".addr, .broker_address"))
        detail["broker_phone"]   = text_or_none(broker_box.locator(".tel, .broker_phone"))

    print(detail)


    return detail

# --- Flask 라우트 ---
@app.route("/crawl", methods=["POST"])
def api_crawl():
    payload = request.get_json(silent=True) or {}
    lat = float(payload.get("lat"))
    lng = float(payload.get("lng"))
    radius_m = payload.get("radius_m") or 800
    category  = payload.get("category") or "offices"
    limit_detail_fetch = int(payload.get("limit_detail_fetch") or 60)

    print(f"[CRAWL IN] lat={lat}, lng={lng}, r={radius_m}, cat={category}, limit={limit_detail_fetch}")
    try:
        # ★ 키워드 인자로 호출 (포지셔널로 넘기면 filters 자리에 박혀서 엉망됨)
        res = crawl_viewport(
            lat, lng,
            radius_m=radius_m,
            category=category,
            limit_detail_fetch=limit_detail_fetch
        )
        print(f"[CRAWL OUT] count={res['meta']['count']}")
        return jsonify(res), 200
    except Exception as e:
        print(f"[CRAWL ERR] {e}")
        return jsonify(ok=False, error="crawl_failed", message=str(e)), 500

if __name__ == "__main__":
    # 리로더/멀티스레드 충돌 방지(먼저 이렇게 확인 후 점진 확장)
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=False)