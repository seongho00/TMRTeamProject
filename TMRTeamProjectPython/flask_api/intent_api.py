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
import cv2, numpy as np, re
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


_BRACKETS = re.compile(r"\[[^\]]+\]")
_CANCEL_RX = re.compile(r"(기?말소|해지)")
_HANGUL_OR_NUM = re.compile(r"[가-힣0-9]")

def _norm_ws(s: str) -> str:
    return " ".join((s or "").replace("\u200b", "").split()).strip()

def _stable_unique(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x); out.append(x)
    return out

def extract_joint_collateral_addresses_follow(
        pdf_bytes: bytes,
        must_have_bracket: bool = True,
        max_follow: int = 6,
):
    """
    【공동담보목록】에서 '부동산에 관한 권리의 표시' 주소만 추출.
    - 첫 페이지: 헤더(부동산/표시) 반드시 찾고 그 열만 사용
    - 이어지는 페이지: 헤더가 없어도 주소열을 '텍스트량/한글+숫자량' 스코어로 추정
    - 같은 행에 '해지/말소/기말소' 포함되면 제외
    """

    def _find_header_top(page):
        txt = page.extract_text() or ""
        if not re.search(r"【\s*공동담보목록\s*】", txt):
            return False, 0.0
        words = page.extract_words(extra_attrs=["top","text"]) or []
        tops = [w["top"] for w in words if "공동담보목록" in (w.get("text") or "")]
        return True, min(tops) if tops else 0.0

    def _extract_tables_on(page, crop_bbox=None):
        tgt = page.within_bbox(crop_bbox) if crop_bbox else page
        tables = []
        try:
            tables = tgt.extract_tables(table_settings={
                "vertical_strategy": "lines",
                "horizontal_strategy": "lines",
                "intersection_x_tolerance": 3,
                "intersection_y_tolerance": 3,
            }) or []
        except Exception:
            pass
        if not tables:
            try:
                tables = tgt.extract_tables() or []
            except Exception:
                tables = []
        return tables

    def _guess_addr_col(tb):
        """헤더가 없을 때 주소열 추정: (한글+숫자 개수 스코어 + 전체 길이 스코어) 최대"""
        if not tb or not tb[0]:
            return None
        cols = max(len(r or []) for r in tb)
        def col_score(i):
            kor_num = 0
            total = 0
            for r in tb[1:]:
                cell = (r[i] if i < len(r) else "") or ""
                t = _norm_ws(str(cell))
                kor_num += len(_HANGUL_OR_NUM.findall(t))
                total += len(t)
            # 한글/숫자 비중을 더 가중
            return kor_num * 2 + total
        scores = [col_score(i) for i in range(cols)]
        return max(range(cols), key=lambda i: scores[i])

    def _pick_addresses_from_tables(tables, require_header: bool, prev_last=None):
        hits = []

        for tb in tables:
            if not tb or not tb[0]:
                continue

            addr_idx = None
            header_row_idx = 0

            if require_header:
                for r_idx, row in enumerate(tb[:5]):
                    header = [(_ or "").strip() for _ in (row or [])]
                    header_txt = " ".join(header)
                    if "부동산" in header_txt and "표시" in header_txt:
                        header_row_idx = r_idx
                        try:
                            addr_idx = next(i for i, h in enumerate(header) if ("부동산" in h and "표시" in h))
                        except StopIteration:
                            addr_idx = None
                        break
                if addr_idx is None:
                    continue
            else:
                addr_idx = _guess_addr_col(tb)
                if addr_idx is None:
                    continue

            # 행 스캔 (hits만 사용)
            for r in tb[header_row_idx+1:]:
                serial = (r[0] or "").strip() if r else ""
                row_text = " ".join((c or "") for c in r)

                cell = r[addr_idx] if addr_idx < len(r) else None
                if not cell or not str(cell).strip():
                    continue
                cleaned = _norm_ws(_BRACKETS.sub(" ", str(cell)))
                if not cleaned:
                    continue

                # 빈 일련번호: 직전 항목에 merge
                if serial == "":
                    target = hits[-1] if hits else prev_last
                    if target is not None:
                        target["address"] += " " + cleaned
                        if _CANCEL_RX.search(row_text):
                            target["status"] = "cancelled"
                    # 붙일 대상이 전혀 없으면 고아 라인 → 스킵
                    continue

                if not serial.isdigit():
                    continue

                status = "cancelled" if _CANCEL_RX.search(row_text) else "normal"
                hits.append({"serial": serial, "address": cleaned, "status": status})

        # 디버깅 (원하면 유지)
        print("pick hits:", hits)
        return hits



    pages_hit, addresses = [], []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        i = 0
        while i < len(pdf.pages):
            page = pdf.pages[i]

            found, header_top = _find_header_top(page)
            if must_have_bracket and not found:
                i += 1
                continue

            crop = (0, header_top, page.width, page.height)

            # 시작 페이지
            prev_last = addresses[-1] if addresses else None
            addrs = _pick_addresses_from_tables(_extract_tables_on(page, crop), require_header=True, prev_last=prev_last)
            if addrs:
                pages_hit.append(i + 1)
                addresses.extend(addrs)

            # 이어지는 페이지
            follow, j = 0, i + 1
            while j < len(pdf.pages) and follow < max_follow:
                tables_j = _extract_tables_on(pdf.pages[j])
                if not tables_j:
                    break

                prev_last = addresses[-1] if addresses else None
                more = _pick_addresses_from_tables(tables_j, require_header=False, prev_last=prev_last)
                if more:
                    pages_hit.append(j + 1)
                    addresses.extend(more)

                follow += 1
                j += 1

            i += 1

    # 여기부터는 addresses가 [ {serial, address, status}, ... ]
    return {"pages": sorted(set(pages_hit)), "addresses": addresses}


# ============ Flask 라우트 ============
@app.route("/analyze", methods=["POST"])
def analyze():
    # 파일 처리
    uploads = []
    if "files" in request.files:
        uploads = request.files.getlist("files")
    elif "file" in request.files:
        uploads = [request.files["file"]]
    if not uploads:
        return jsonify(ok=False, message="PDF 파일이 없습니다."), 400
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

    try:
        joint_info = extract_joint_collateral_addresses_follow(data)
    except Exception as e:
        import traceback;
        traceback.print_exc()
        return jsonify(ok=False, message=f"분석 실패: {e}"), 500

    print(doc)
    return jsonify(
        ok=True,
        pageCount=len(doc),
        jointCollateralPages=joint_info["pages"],
        jointCollateralAddresses=joint_info["addresses"]
    ), 200


# 좌표를 통한 네이버 부동산 실시간 크롤링
# --- Playwright 설정 ---
USER_DATA_DIR = "./.chrome-profile"  # 쿠키/지문 유지
HEADLESS = False  # 먼저 창 띄워서 확인 후 True로 전환 가능
LIST_SEL_CANDS = [
    "div.item_list.item_list--article",
    "div.item_list--article",
    "div.article_list",  # 예비
]
API_SOFT_WAIT_MS = 1200  # 800~1500 권장 (너무 느리면 900로)
MAX_CLICK = 20  # 클릭할 카드 수 상한


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
        page.locator(sel).click(position={"x": 10, "y": 10}, timeout=1000)
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
    for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy"):
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
            "--no-first-run", "--no-default-browser-check",
            "--disable-dev-shm-use", "--no-sandbox",
        ],
    )
    # 약식 스텔스
    ctx.add_init_script("""
      Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
      Object.defineProperty(navigator, 'language', {get: () => 'ko-KR'});
      Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR','ko','en-US','en']});
      window.chrome = window.chrome || { runtime: {} };
    """)
    ctx.set_extra_http_headers({"Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7"})
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
                dom_data = scrape_detail_panel(page)  # 또는 scrape_detail_panel_raw(page)
            except Exception:
                dom_data = {}

            detail_hits.append({
                "url": (hit["url"] if hit else None),
                "status": (hit["status"] if hit else None),
                "json": (hit["data"] if hit else None),
                "dom": dom_data,
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
            "items": detail_hits[:limit],  # limit=None이면 전부
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
    detail["price_type"] = text_or_none(price_box.locator(".type"))  # 예: "월세"
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
        detail["broker_name"] = text_or_none(broker_box.locator(".name, .broker_name"))
        detail["broker_ceo"] = text_or_none(broker_box.locator(".ceo, .broker_ceo"))
        detail["broker_address"] = text_or_none(broker_box.locator(".addr, .broker_address"))
        detail["broker_phone"] = text_or_none(broker_box.locator(".tel, .broker_phone"))

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
    per_sqm_vals: List[float] = []  # 만원/㎡
    per_pyeong_vals: List[float] = []  # 만원/평

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

        per_sqm = monthly / area  # 만원/㎡
        per_pyeong = monthly / (area / 3.305785)  # 만원/평

        per_sqm_vals.append(per_sqm)
        per_pyeong_vals.append(per_pyeong)

        def _avg(vs: List[float]) -> Optional[float]:
            return round(sum(vs) / len(vs), 3) if vs else None

    return {
        "count": len(per_sqm_vals),
        "avg_per_sqm_manwon": _avg(per_sqm_vals),  # 만원/㎡
        "avg_per_pyeong_manwon": _avg(per_pyeong_vals),  # 만원/평
    }


# --- Flask 라우트 ---
@app.route("/crawl", methods=["POST"])
def api_crawl():
    payload = request.get_json(silent=True) or {}
    lat = float(payload.get("lat"))
    lng = float(payload.get("lng"))
    radius_m = payload.get("radius_m") or 800
    category = payload.get("category") or "offices"
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

        stats = avg_monthly_by_area(res["items"])
        print("[면적 구간별 평균 월세]", stats)

        print(f"[CRAWL OUT] count={res['meta'].get('count_detail', len(res.get('items', [])))}")
        return jsonify(res), 200
    except Exception as e:
        print(f"[CRAWL ERR] {e}")
        return jsonify(ok=False, error="crawl_failed", message=str(e)), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=False)
