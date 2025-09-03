from collections import deque
from contextlib import nullcontext

from flask import Flask, request, jsonify, Response
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pickle
import mecab_ko
import pymysql
import pymysql.cursors
import io, os, uuid, tempfile
import re, time, random, hashlib
from collections import deque
import io
import pdfplumber
import fitz  # ← PyMuPDF
from playwright.sync_api import Page, Locator, TimeoutError as PWTimeout
# HEIC 지원 (설치되어 있으면 자동 등록)
try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception:
    pass

# 크롤링 관련 import
from typing import Optional, Collection, List, Dict, Tuple, Any, Set
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

# 업종 검색 관련 import
import re
import unicodedata

try:
    from rapidfuzz import process, fuzz
    HAVE_RAPIDFUZZ = True
except Exception:
    HAVE_RAPIDFUZZ = False

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

            print(name_to_code)

            return name_to_code
    except Exception as e:
        print("❌ 업종 코드 로딩 실패:", e)
        return {}
    finally:
        conn.close()

def _normalize(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    # 환경에 따라 아래 둘 중 하나 사용
    s = re.sub(r'[^0-9A-Za-z\u3131-\u318E\uAC00-\uD7A3]+', '', s)  # 권장 대안
    # s = re.sub(r'[\s\p{P}\p{S}]+', '', s)
    return s

def find_upjong_pre_morph_from_map(
        user_input: str,
        name_to_code: dict[str, str],   # {"중국음식점":"CS1001", ...}
        fuzzy_threshold: int = 60,
        max_window_len: int = 12
):
    """
    반환: (raw_phrase, mapped_name, mapped_code, score, method)
    실패: (None, None, None, None, None)
    """
    text_norm = _normalize(user_input)
    if not text_norm:
        return (None, None, None, None, None)

    # 정규화 인덱스
    idx = { _normalize(nm): (nm, code) for nm, code in name_to_code.items() }

    # 1) 공백무시 부분일치(가장 긴 매칭 우선)
    best = None
    for nm_norm, (nm, cd) in idx.items():
        if nm_norm in text_norm:
            cand = (nm, nm, cd, 100, "substring")
            if not best or len(nm) > len(best[0]):
                best = cand
    if best:
        return best

    # 2) 퍼지 매칭(옵션)
    if HAVE_RAPIDFUZZ:
        keys = list(idx.keys())
        BEST = (None, None, None, -1, "fuzzy")
        Lmax = min(max_window_len, max((len(k) for k in keys), default=0))
        for L in range(2, Lmax + 1):
            for i in range(0, max(0, len(text_norm) - L + 1)):
                sub = text_norm[i:i+L]
                m = process.extractOne(sub, keys, scorer=fuzz.ratio)
                if m and m[1] > BEST[3]:
                    nm, cd = idx[m[0]]
                    BEST = (sub, nm, cd, m[1], "fuzzy")
        if BEST[3] >= fuzzy_threshold:
            return BEST

    return (None, None, None, None, None)

# ✅ 의미 분석 함수
def analyze_input(user_input, intent, valid_emd_list):


    entities = {
        "sido": None,
        "sigungu": None,
        "emd_nm": None,
        "gender": None,
        "age_group": None,
        "upjong_cd": None,
        "raw_upjong": None,  # 매칭 안 되면 원문 보관
    }

    # 업종 선매핑 (동의어 없이)
    raw, nm, cd, score, method = find_upjong_pre_morph_from_map(
        user_input, upjong_keywords, fuzzy_threshold=80
    )
    if cd:
        entities["raw_upjong"] = raw or nm
        entities["upjong_nm"]  = nm
        entities["upjong_cd"]  = cd

    tokens = extract_nouns_with_age_merge(user_input)
    print("추출된 명사:", tokens)

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
        if entities["upjong_cd"] is None:
            if t in upjong_keywords:  # 기존 키워드 사전 (간단 매핑용)
                entities["upjong_cd"] = upjong_keywords[t]
                entities["upjong_nm"] = t
                entities["raw_upjong"] = t
            else:
                # 일상어 힌트만 기록
                if t in ("카페", "편의점", "분식", "패스트푸드", "의류", "중국집", "치킨집"):
                    entities["raw_upjong"] = t

    # 지역 최소 단위 판정(하나라도 있으면 OK)
    has_region = bool(entities["emd_nm"] or entities["sigungu"] or entities["sido"])

    # 누락 항목 계산
    required = INTENT_REQUIRED.get(intent, {"need": [], "optional": []})
    missing = []

    if "sido_or_sigungu_or_emd" in required["need"] and not has_region:
        missing.append("region")  # 지역(시/구/동 중 하나)

    # 다른 의무 파라미터가 필요하면 여기에 조건 추가(예: intent별 필수 성별 등)
    print(entities)
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

_WS = re.compile(r"\s+")
_MONEY = re.compile(r"금?\s*([0-9,]+)\s*원")

# '말소/해지' 플래그만 확인
_CANCEL_FLAG_RX   = re.compile(r"(말소|해지)")
# 보조: purpose 텍스트에서 "1번 근저당권 설정" 같은 표기를 파싱 (순위번호 칸이 비었을 때만 사용)
_CANCEL_TARGET_RX = re.compile(r"(\d+)\s*번")
# 취소 대상 번호들: "제1번", "1번", "1,2번", "1번·2번" 등에서 모두 추출
_RANK_LIST_RX = re.compile(r"(?:제?\s*)(\d+)\s*번")

_RISK_FLAG_RX = re.compile(r"(가압류|가처분|압류)")

def _one_line(s: str) -> str:
    return _WS.sub(" ", (s or "").strip())

def _parse_amount_num(text: str):
    m = _MONEY.search(text or "")
    if not m:
        return None
    try:
        return int(m.group(1).replace(",", ""))
    except:
        return None

def extract_mortgage_info(pdf_bytes: bytes):
    """
    【을구】에서 근저당권 '설정'만 수집하고,
    '말소/해지' 행은 '해당 행의 순위번호'를 취소 대상으로 간주.
    반환: [{"rankNo": int, "amountKRW": int|None, "status": "normal|cancelled"} ...]
    """
    title_rx = re.compile(r"【\s*을\s*구\s*】")

    mortgages_by_rank = {}   # rankNo -> {"rankNo", "amountKRW", "status"}
    cancel_ranks = set()     # 말소/해지로 지목된 순위번호들
    risks = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            if not title_rx.search(txt):
                continue

            tables = page.extract_tables() or []
            for tb in tables:
                if not tb:
                    continue

                # 헤더 위치 추정
                col_rank = col_purpose = col_amount = None
                for row in tb[:5]:
                    cells = [(_one_line(c) if c else "") for c in (row or [])]
                    for i, c in enumerate(cells):
                        if col_rank is None    and (c in ("순위번호","순위")):    col_rank = i
                        if col_purpose is None and ("등기" in c and "목적" in c):  col_purpose = i
                        if col_amount is None  and ("채권최고액" in c):            col_amount = i
                if col_rank   is None: col_rank = 0
                if col_purpose is None: col_purpose = 1
                if col_amount is None:  col_amount = 4

                for row in tb:
                    if not row or len(row) <= max(col_rank, col_purpose, col_amount):
                        continue

                    rank_raw   = _one_line(row[col_rank])
                    purpose    = _one_line(row[col_purpose])
                    amount_txt = _one_line(row[col_amount])

                    # --- 1) 말소/해지 행: 텍스트 안의 "…번"들만 취소 대상으로 수집 ---
                    if _CANCEL_FLAG_RX.search(purpose):
                        nums = _RANK_LIST_RX.findall(purpose)  # ["1","2",...]
                        for n in nums:
                            cancel_ranks.add(int(n))
                        continue  # 말소행 자체는 수집 안 함

                    # --- 근저당권 '설정'만 수집 ---
                    if ("근저당권" in purpose) and ("설정" in purpose):
                        # 순위번호 열이 숫자여야 설정행으로 인정
                        if rank_raw.isdigit():
                            row_rank = int(rank_raw)
                            mortgages_by_rank[row_rank] = {
                                "rankNo": row_rank,
                                "amountKRW": _parse_amount_num(amount_txt),
                                "status": "normal",
                            }

                    if _RISK_FLAG_RX.search(purpose):
                        risks.append({
                            "rankNo": int(rank_raw) if rank_raw.isdigit() else None,
                            "purpose": purpose
                        })

    # 말소 대상 순위를 취소 처리
    for r in cancel_ranks:
        if r in mortgages_by_rank:
            mortgages_by_rank[r]["status"] = "cancelled"

    # 설정행만 정렬해서 반환
    return {
        "mortgages": sorted(mortgages_by_rank.values(), key=lambda x: x["rankNo"]),
        "riskFlags": risks
    }
def extract_joint_collateral_addresses_follow(
        pdf_bytes: bytes,
        must_have_bracket: bool = True,
        max_follow: int = 6,
):
    """
    【공동담보목록】에서 '부동산에 관한 권리의 표시' 주소만 추출. + [집합건물] 현재주소 추가
    - 첫 페이지: 헤더(부동산/표시) 반드시 찾고 그 열만 사용
    - 이어지는 페이지: 헤더가 없어도 주소열을 '텍스트량/한글+숫자량' 스코어로 추정
    - 같은 행에 '해지/말소/기말소' 포함되면 제외
    """

    # [집합건물] 뒤 주소 추출
    def _extract_current_address(pdf):
        for page in pdf.pages:
            txt = page.extract_text() or ""
            m = re.search(r"\[집합건물\]\s*(.+)", txt)
            if m:
                return _norm_ws(m.group(1))
        return None

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

        return hits



    pages_hit, addresses = [], []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:

        # 현재주소 먼저 뽑기
        current_addr = _extract_current_address(pdf)

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
    return {"pages": sorted(set(pages_hit)), "addresses": addresses, "currentAddress": current_addr}

_OWNER_CHANGE_RX = re.compile(r"소유권.*이전")
_CO_OWNER_RX     = re.compile(r"공유")

# 갑구 분석
def extract_gabu_info(pdf_bytes: bytes):
    """
    【갑구】에서 소유권 변경 이력, 공동소유 여부 추출
    반환:
    {
        "ownerChangeCount": int,
        "ownerChangeDetails": [ ... ],
        "coOwners": bool
    }
    """
    title_rx = re.compile(r"【\s*갑\s*구\s*】")
    owner_changes = []
    co_owners = False

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            txt = page.extract_text() or ""
            if not title_rx.search(txt):
                continue

            tables = page.extract_tables() or []
            for tb in tables:
                if not tb:
                    continue

                for row in tb:
                    cells = [(_one_line(c) if c else "") for c in (row or [])]
                    if not cells:
                        continue
                    purpose = cells[1] if len(cells) > 1 else ""   # 등기목적
                    right_holder = cells[2] if len(cells) > 2 else ""  # 권리자/기타사항

                    # 소유권 이전 탐지
                    if _OWNER_CHANGE_RX.search(purpose):
                        owner_changes.append(purpose)

                    # 공유자 여부 탐지
                    if _CO_OWNER_RX.search(right_holder):
                        co_owners = True

    return {
        "ownerChangeCount": len(owner_changes),
        "ownerChangeDetails": owner_changes,
        "coOwners": co_owners
    }
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
        mortgage_info = extract_mortgage_info(data)
        gabu_info = extract_gabu_info(data)
    except Exception as e:
        import traceback;
        traceback.print_exc()
        return jsonify(ok=False, message=f"분석 실패: {e}"), 500


    return jsonify(
        ok=True,
        pageCount=len(doc),
        jointCollateralPages=joint_info["pages"],
        jointCollateralAddresses=joint_info["addresses"],
        jointCollateralCurrentAddress= joint_info["currentAddress"],
        mortgageInfo = mortgage_info["mortgages"],
        mortgageRiskFlags=mortgage_info["riskFlags"],  # 가압류/압류/가처분
        gabuInfo=gabu_info
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
API_SOFT_WAIT_MS = 800  # 800~1500 권장 (너무 느리면 900로)
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
    path = f"/offices?ms={lat},{lng},19&a=SG&e=RETAIL"
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
            page.wait_for_timeout(10)  # 패널 렌더 여유
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


def parse_korean_price(s: str) -> Optional[int]:
    """한국식 금액 문자열(예: 1억400, 2,000, 3500)을 만원 단위 정수로 변환"""
    if not s:
        return None

    s = s.replace(",", "").strip()
    total = 0

    # 억 단위 (1억 = 10000만원)
    match = re.search(r"(\d+)억", s)
    if match:
        total += int(match.group(1)) * 10000
        s = s[match.end():]

    # 남은 숫자 (만원 단위)
    digits = re.findall(r"\d+", s)
    if digits:
        total += int("".join(digits))

    return total if total > 0 else None


def parse_deposit_monthly(price_value: Optional[str]) -> Tuple[Optional[int], Optional[int]]:
    """'보증금/월세' 문자열을 (보증금, 월세) 튜플로 변환 (만원 단위)"""
    if not price_value:
        return None, None

    if "/" not in price_value:  # 전세 or 매매 (단일 금액)
        return parse_korean_price(price_value), None

    a, b = price_value.split("/", 1)
    return parse_korean_price(a), parse_korean_price(b)


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
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False, threaded=False)
