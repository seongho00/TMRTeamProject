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
import re, time, random, hashlib
from collections import deque
from playwright.sync_api import sync_playwright, Page
import io
import pdfplumber
import fitz  # ← PyMuPDF


# HEIC 지원 (설치되어 있으면 자동 등록)
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except Exception:
    pass

# 크롤링 관련 import
from typing import Optional, Collection, List, Dict, Tuple, Any, Set
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout


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
# ------------------------- 텍스트 유틸 -------------------------
def squash_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def extract_pages_text_textonly(doc: fitz.Document) -> List[str]:
    """OCR 없이 PDF 내 텍스트만 추출"""
    pages = []
    for i in range(len(doc)):
        txt = doc[i].get_text("text") or ""
        pages.append(txt)
    return pages

def extract_tables_textbased(pdf_bytes: bytes) -> List[Dict[str, Any]]:
    """pdfplumber로 선/텍스트 기반 테이블 추출(있으면) → TSV"""
    out = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for pidx, page in enumerate(pdf.pages, start=1):
            tables = []
            # 라인 기반 시도
            try:
                tables = page.extract_tables(table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines",
                    "intersection_x_tolerance": 3,
                    "intersection_y_tolerance": 3
                }) or []
            except Exception:
                pass
            # 실패하면 기본 전략
            if not tables:
                try:
                    tables = page.extract_tables() or []
                except Exception:
                    tables = []
            for t in tables:
                lines = ["\t".join("" if c is None else str(c) for c in row) for row in t]
                out.append({"page": pidx, "tsv": "\n".join(lines)})
    return out

# ------------------------- 간단 파서(기존 베이스) -------------------------
SEC_RE = {
    "표제부": re.compile(r"(표제부.*?)(?=갑구|을구|$)", re.S),
    "갑구":   re.compile(r"(갑구.*?)(?=표제부|을구|$)", re.S),
    "을구":   re.compile(r"(을구.*?)(?=표제부|갑구|$)", re.S),
}

def split_sections(text: str) -> dict:
    secs = {}
    for k, rx in SEC_RE.items():
        m = rx.search(text)
        secs[k] = m.group(1) if m else ""
    return secs

def simple_parse(full_text: str) -> Dict[str, Any]:
    header = {}
    m = re.search(r"\[집합건물\].*", full_text)
    if m: header["building_line"] = squash_ws(m.group(0))
    m = re.search(r"발행번호\s*([A-Z0-9\-]+)", full_text)
    if m: header["publish_no"] = m.group(1)
    m = re.search(r"발급확인번호\s*([A-Z0-9\-]+)", full_text)
    if m: header["verify_no"] = m.group(1)
    m = re.search(r"발행일\s*(\d{4}[./-]\d{1,2}[./-]\d{1,2})", full_text)
    if m: header["publish_date"] = m.group(1).replace(".", "/")

    # 표제부 예시: '1층 401.08㎡'
    floors = []
    for fl, area in re.findall(r"(\d+층)\s+([\d,]+(?:\.\d+)?)㎡", full_text):
        try:
            floors.append({"층": fl, "면적_㎡": float(area.replace(",", ""))})
        except:
            pass

    # 대지권 비율 예시: '358분의 3.84'
    land_shares = []
    for denom, numer in re.findall(r"([\d\.]+)\s*분의\s*([\d\.]+)", full_text):
        try:
            land_shares.append({"base": float(denom), "share": float(numer)})
        except:
            pass

    # 섹션 자르기
    def section(name, after):
        m = re.search(r"【\s*" + name + r"\s*구\s*】", full_text)
        if not m:
            return None
        s = m.end()
        e = len(full_text)
        mm = re.search(r"【\s*(?:" + after + r")\s*】", full_text[s:])
        if mm:
            e = s + mm.start()
        return full_text[s:e]

    gap = section("갑", "을|공동담보목록")
    eul = section("을", "공동담보목록")

    return {
        "header": header,
        "pyojebu": {"floors": floors},
        "daejigwon": {"shares": land_shares},
        "gapgu_raw": squash_ws(gap) if gap else None,
        "eulgu_raw": squash_ws(eul) if eul else None,
    }

# ------------------------- 요약(주소/채권최고액/공동담보 주소) -------------------------
KOR_DATE_RE = re.compile(r"(?P<y>\d{4})\s*년\s*(?P<m>\d{1,2})\s*월\s*(?P<d>\d{1,2})\s*일")
WON_DIGIT_RE = re.compile(r"채권최고액\s*금?\s*(?P<amt>[0-9][0-9,]*)\s*원")
BRACKET_ADDR_RE = re.compile(r"\[.*?집합건물.*?\]\s*(?P<line>.+)")

def _to_date_yyyy_mm_dd(s: str) -> Optional[str]:
    m = KOR_DATE_RE.search(s)
    if not m:
        return None
    y, mth, d = int(m.group("y")), int(m.group("m")), int(m.group("d"))
    return f"{y:04d}-{mth:02d}-{d:02d}"

def _to_won_int(s: str) -> Optional[int]:
    s = s.strip().replace(",", "")
    return int(s) if s.isdigit() else None

def extract_subject_address(full_text: str) -> Optional[str]:
    m = BRACKET_ADDR_RE.search(full_text)
    if m:
        return m.group("line").strip()
    # fallback: 지번 주소 패턴
    addr_re = re.compile(r"[가-힣]+(특별시|광역시|도|시)\s+[가-힣0-9]+(구|군|시)\s+[가-힣0-9]+(동|읍|면)\s+[0-9\-]+(?:번지)?")
    m2 = addr_re.search(full_text)
    return m2.group(0).strip() if m2 else None

def extract_eulgu_block(full_text: str) -> str:
    m = re.search(r"【\s*을\s*구\s*】(?P<blk>[\s\S]+?)(?:【\s*갑\s*구\s*】|---PAGEBREAK---|\Z)", full_text)
    return m.group("blk") if m else full_text

def parse_mortgages_from_eulgu(eul_text: str) -> List[Dict[str, Any]]:
    results = []
    mort_re = re.compile(
        r"^\s*(?P<idx>\d+)\s+근저당권설정\b(?P<tail>[\s\S]*?)(?=^\s*\d+\s+\S|\Z)",
        re.MULTILINE
    )
    for m in mort_re.finditer(eul_text):
        idx = m.group("idx")
        block = m.group("tail")
        reg_date = _to_date_yyyy_mm_dd(block)  # 블럭에서 첫 한글날짜 추정
        amt = None
        m_amt = WON_DIGIT_RE.search(block)
        if m_amt:
            amt = _to_won_int(m_amt.group("amt"))
        joint_id = None
        m_joint = re.search(r"공동담보목록\s*제?\s*(?P<id>\d{4}-\d+)\s*호", block)
        if m_joint:
            joint_id = m_joint.group("id")
        results.append({
            "order_no": int(idx),
            "registered_at": reg_date,
            "max_claim_won": amt,
            "joint_list_id": joint_id,
            "cancelled": False,
            "raw": block.strip()[:500]
        })

    # 'N번근저당권설정등 ... 기말소 ... 해지' → N번 말소 처리
    cancel_re = re.compile(r"^\s*(?P<idx>\d+)\s+(?P<ref>\d+)번근저당권설정등[\s\S]*?기말소[\s\S]*?해지", re.MULTILINE)
    cancelled_refs = {int(c.group("ref")) for c in cancel_re.finditer(eul_text)}
    for r in results:
        if r["order_no"] in cancelled_refs:
            r["cancelled"] = True
    return results

def extract_joint_collateral_addresses(full_text: str) -> List[str]:
    out, seen = [], set()
    for m in re.finditer(r"(공동담보목록\s*제?\s*\d{4}-\d+\s*호)(?P<blk>[\s\S]+?)(?:---PAGEBREAK---|발행번호|【|\Z)", full_text):
        blk = m.group("blk")
        addr_pats = [
            r"[가-힣]+(특별시|광역시|도|시)\s+[가-힣0-9]+(구|군|시)\s+[가-힣0-9]+(동|읍|면)\s+\d+(?:-\d+)?번지(?:\s*외\s*\d+\s*필지)?",
            r"[가-힣]+(특별시|광역시|도|시)\s+[가-힣0-9]+(구|군|시)\s+[^\s]+(로|길)[^\s]*\s+\d+(?:-\d+)?(?:\s*\([^)]+\))?"
        ]
        for pat in addr_pats:
            for a in re.finditer(pat, blk):
                addr = a.group(0).strip()
                if addr not in seen:
                    seen.add(addr)
                    out.append(addr)
    return out

# ------------------------- 라우트 -------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    # 'files' 또는 'file' 어느 쪽이든 수용
    uploads = []
    if "files" in request.files:
        uploads = request.files.getlist("files")
    elif "file" in request.files:
        uploads = [request.files["file"]]

    if not uploads:
        return jsonify(ok=False, message="PDF 파일이 없습니다. (필드: files 또는 file)"), 400
    if len(uploads) > 1:
        return jsonify(ok=False, message="PDF는 1개만 업로드하세요."), 400

    up = uploads[0]
    data = up.read() or b""
    if b"%PDF-" not in data[:1024] and b"%PDF-" not in data:
        return jsonify(ok=False, message="PDF만 허용합니다."), 415

    try:
        doc = fitz.open(stream=data, filetype="pdf")
    except Exception as e:
        return jsonify(ok=False, message=f"PDF 열기 실패: {e}"), 400

    # 1) 텍스트 추출
    pages = extract_pages_text_textonly(doc)
    full_text = "\n\n---PAGEBREAK---\n\n".join(pages)

    # 2) (선택) 텍스트 기반 테이블
    tables = extract_tables_textbased(data)

    # 3) 네 기존 최소 파서
    parsed = simple_parse(full_text)

    # 4) 요약 생성
    subject_addr = extract_subject_address(full_text)

    eul_text = parsed.get("eulgu_raw") if isinstance(parsed, dict) else None
    if not eul_text:
        eul_text = extract_eulgu_block(full_text)

    mortgages = parse_mortgages_from_eulgu(eul_text)
    total_max_claim_active = sum(m["max_claim_won"] or 0 for m in mortgages if not m["cancelled"])
    joint_addresses = extract_joint_collateral_addresses(full_text)
    print(mortgages)
    print(subject_addr)
    print(total_max_claim_active)
    print(joint_addresses)



    return jsonify(
        ok=True,
        pageCount=len(doc),
        textPreview=full_text[:2000],
        parsed=parsed,
        tables_textbased=tables,
        summary=dict(
            subject_address=subject_addr,
            mortgages=mortgages,                 # [{order_no, registered_at, max_claim_won, joint_list_id, cancelled, raw}]
            total_active_max_claim=total_max_claim_active,
            joint_collateral_addresses=joint_addresses
        )
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
        for i, c in enumerate(cards):  # ✅ 모든 카드 순회
            if limit_detail_fetch and len(detail_hits) >= int(limit_detail_fetch):
                break

            try:
                before_len = len(api_detail_queue)
                c.scroll_into_view_if_needed()
                c.click()
            except Exception:
                continue

            # API는 최대 1.2초만 소프트 대기 (없어도 통과)
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

            page.wait_for_timeout(120 + int(random.random() * 120))

        # 정리
        ctx.close()

        # 모든 항목 반환 (limit_detail_fetch가 None이면 전부)
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
            "items": detail_hits[:limit],   # limit=None이면 전부
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
        "전용면적": ["전용면적"],
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

# ── ㎡ 파싱: 문자열에서 "…㎡" 값들만 뽑아 '가장 작은 ㎡'를 전용면적으로 간주 ──
# 예) "50㎡/38.6㎡(전용률80%)" → [50.0, 38.6] → 38.6
def _extract_area_sqm(val: Optional[str]) -> Optional[float]:
    if val is None:
        return None
    s = str(val)
    matches = re.findall(r"([\d]+(?:\.\d+)?)\s*(?:㎡|m²)", s, flags=re.IGNORECASE)
    if matches:
        nums = [float(x) for x in matches]
        return min(nums)  # 보통 전용(㎡)이 더 작음
    # "14평" 같은 경우를 대비(있다면)
    m_py = re.search(r"([\d]+(?:\.\d+)?)\s*평", s)
    if m_py:
        return round(float(m_py.group(1)) * 3.305785, 3)
    return None

# ── 핵심: 월세만 필터 → 면적 뽑기 → 구간별 평균 월세 계산 ─────────────
def avg_monthly_by_area(detail_hits: List[Dict[str, Any]]) -> Dict[str, float]:
    per_sqm_vals: List[float] = []      # 만원/㎡
    per_pyeong_vals: List[float] = []   # 만원/평

    for it in detail_hits:
        d = it.get("dom") or {}
        if not d:
            continue

        # 월세만
        price_type = str(d.get("price_type") or "")
        if "월세" not in price_type:
            continue

        # 월세 금액
        monthly: Optional[int] = d.get("monthly")

        # 면적: 전용면적 우선, 없으면 공급면적 시도
        area_str = d.get("전용면적")
        area = _extract_area_sqm(area_str)


        if monthly is None or area is None:
            continue

        per_sqm = monthly / area                     # 만원/㎡
        per_pyeong = monthly / (area / 3.305785)     # 만원/평

        per_sqm_vals.append(per_sqm)
        per_pyeong_vals.append(per_pyeong)

        def _avg(vs: List[float]) -> Optional[float]:
            return round(sum(vs) / len(vs), 3) if vs else None

    return {
        "count": len(per_sqm_vals),
        "avg_per_sqm_manwon": _avg(per_sqm_vals),         # 만원/㎡
        "avg_per_pyeong_manwon": _avg(per_pyeong_vals),   # 만원/평
    }
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
        res =   crawl_viewport(
            lat, lng,
            radius_m=radius_m,
            category=category,
            limit_detail_fetch=limit_detail_fetch
        )

        stats = avg_monthly_by_area(res["items"])
        print("[면적 구간별 평균 월세]", stats)

        print(f"[CRAWL OUT] count={res['meta'].get('count_detail', len(res.get('items', [])))}")
        return jsonify(res), 200
    except Exception as e:
        print(f"[CRAWL ERR] {e}")
        return jsonify(ok=False, error="crawl_failed", message=str(e)), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=False)