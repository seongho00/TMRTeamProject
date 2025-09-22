import io
import os
import pickle
import random
import time
from collections import deque
from contextlib import nullcontext
from collections import defaultdict
from flask import Flask, request, jsonify, Response
import torch
from transformers import BertTokenizer, BertForSequenceClassification
import pickle
import mecab_ko
import pdfplumber
import pymysql
import pymysql.cursors
import io, os, uuid, tempfile
import re, time, random, hashlib
from collections import deque
from decimal import Decimal, InvalidOperation

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
from typing import Optional, List, Dict, Tuple, Any, Set
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
        name_to_code: dict[str, str],  # {"중국음식점":"CS1001", ...}
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
    idx = {_normalize(nm): (nm, code) for nm, code in name_to_code.items()}

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
                sub = text_norm[i:i + L]
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

    # 1) (가장 먼저) 문자열 기반 행정동 인식
    emd_index = build_emd_index(valid_emd_list)  # 실서비스는 모듈 로드시 1회만
    emd_hits = find_emd_in_text(user_input, emd_index)
    if emd_hits:
        entities["emd_nm"] = emd_hits[0]  # 여러 개면 첫 번째를 기본값으로

    # 업종 선매핑 (동의어 없이)
    raw, nm, cd, score, method = find_upjong_pre_morph_from_map(
        user_input, upjong_keywords, fuzzy_threshold=80
    )
    if cd:
        entities["raw_upjong"] = raw or nm
        entities["upjong_nm"] = nm
        entities["upjong_cd"] = cd

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

# 1) 한글+숫자만 남기고 나머지 제거
_NORM_RE = re.compile(r'[^가-힣0-9]')

def normalize_kr(s: str) -> str:
    return _NORM_RE.sub('', s or '')

_ENUM_SEP_RE = re.compile(r'[·ㆍ\.\,\/]')

# 예: "종로1·2·3·4가동"  /  "명륜1·2가동"
#  - prefix: "종로" / "명륜"
#  - numseq: "1·2·3·4" / "1·2"
#  - suf   : "가동" (또는 "동", "가")
_ENUM_PATTERN = re.compile(
    r'^(?P<prefix>[가-힣]+)\s*(?P<numseq>\d+(?:[·ㆍ\.\,\/]\d+)+)\s*(?P<suf>가동|동|가)$'
)

def gen_emd_variants(name: str) -> Set[str]:
    """
    공식 행정동명 하나로부터 매칭에 사용할 '정규화 변형문자열' 집합 생성.
    - 묶음형(종로1·2·3·4가동) → 각 번호별 파생(종로1가동, 종로2가동, ...)
    - '가동'인 경우, 사람들이 많이 치는 '종로3가'도 허용 (규칙 기반, 별칭 테이블 아님)
    - '제숫자' ↔ '숫자' 변형도 양방향 생성
    """
    variants: Set[str] = set()
    raw = (name or '').strip()

    # 기본형(공식명 자체)
    base_norm = normalize_kr(raw)
    if base_norm:
        variants.add(base_norm)

    # 1) 번호 나열(·/ㆍ/./,/ /)이 들어간 묶음형일 경우 → 자동 분해
    m = _ENUM_PATTERN.match(raw)
    if m:
        prefix = m.group('prefix')
        numseq = m.group('numseq')
        suf    = m.group('suf')  # '가동' | '동' | '가'
        nums = [n for n in _ENUM_SEP_RE.split(numseq) if n]

        for num in nums:
            # ex) 종로3가동
            cand = f"{prefix}{num}{suf}"
            variants.add(normalize_kr(cand))
            # 사람들이 자주 치는 형태: '가동'이면 '...가'도 허용 (ex: 종로3가)
            if suf == '가동':
                variants.add(normalize_kr(f"{prefix}{num}가"))

            # '제숫자' 표기 허용 (제3가동 / 제3가)
            variants.add(normalize_kr(f"{prefix}제{num}{suf}"))
            if suf == '가동':
                variants.add(normalize_kr(f"{prefix}제{num}가"))

        return variants  # 묶음형이면 여기서 끝

    # 2) 일반형: '제숫자접미' ↔ '숫자접미' 양방향
    #   예) '창신제1동' → '창신1동',  '창신1동' → '창신제1동'
    m2 = re.search(r'제(\d+)(동|가동|읍|면|리|가)$', raw)
    if m2:
        num, suf = m2.groups()
        variants.add(normalize_kr(re.sub(r'제(\d+)(동|가동|읍|면|리|가)$', f'{num}{suf}', raw)))

    m3 = re.search(r'(\d+)(동|가동|읍|면|리|가)$', raw)
    if m3:
        num, suf = m3.groups()
        variants.add(normalize_kr(re.sub(r'(\d+)(동|가동|읍|면|리|가)$', f'제{num}{suf}', raw)))

    return variants

# 3) (초기화 시 1회) 행정동 인덱스 구축: 변형들 -> 원본명 매핑
def build_emd_index(valid_emd_list: List[str]) -> Dict[str, str]:
    index = {}
    for emd in valid_emd_list:
        for v in gen_emd_variants(emd):
            # 같은 키가 여러 원본에 매핑되면 더 긴(특이성이 높은) 원본을 우선
            if v not in index or len(emd) > len(index[v]):
                index[v] = emd
    return index

# 4) 원문에서 최장일치 탐색 (토큰 무시, 문자열 기반)
def find_emd_in_text(user_input: str, emd_index: Dict[str, str]) -> List[str]:
    """
    정규화된 입력에서 사전 키(정규화된 변형)들을 길이순으로 스캔해 최장일치로 뽑는다.
    입력 길이가 짧으니 O(N*M) 단순 스캔으로도 충분히 빠름.
    """
    text = normalize_kr(user_input)
    if not text:
        return []

    # 키들을 길이 긴 순으로 정렬 → 최장일치 우선
    keys = sorted(emd_index.keys(), key=len, reverse=True)

    hits = []
    used = [False] * len(text)  # 겹침 방지용 마스크

    def can_place(start: int, end: int) -> bool:
        return all(not used[i] for i in range(start, end))

    def place(start: int, end: int):
        for i in range(start, end):
            used[i] = True

    for k in keys:
        start = 0
        while True:
            idx = text.find(k, start)
            if idx == -1:
                break
            j = idx + len(k)
            if can_place(idx, j):
                place(idx, j)
                hits.append(emd_index[k])  # 원본명 저장
            start = idx + 1

    # 중복 제거, 입력 내 등장 순서 유지
    seen = set()
    ordered = []
    for h in hits:
        if h not in seen:
            seen.add(h)
            ordered.append(h)
    return ordered

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
            "entities": entities,  # ← 지역, 업종, 성별, 연령 등 전체 전달
            "data": "...매출조회결과..."
        }), 200

    elif intent_id == 1:  # 유동인구
        return jsonify({
            "intent": 1,
            "confidence": round(confidence, 4),
            "entities": entities,  # ← 지역, 업종, 성별, 연령 등 전체 전달
            "data": "...매출조회결과..."
        }), 200


    elif intent_id == 2:  # 위험도
        return jsonify({
            "intent": 2,
            "confidence": round(confidence, 4),
            "entities": entities,  # ← 지역, 업종, 성별, 연령 등 전체 전달
            "data": "...매출조회결과..."
        }), 200

    else:  # intent_id == 3 등
        return jsonify({
            "intent": int(intent_id),
            "confidence": round(confidence, 4),
            "entities": entities,  # ← 지역, 업종, 성별, 연령 등 전체 전달
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
            seen.add(x);
            out.append(x)
    return out


_WS = re.compile(r"\s+")
_MONEY = re.compile(r"금?\s*([0-9,]+)\s*원")

# '말소/해지' 플래그만 확인
_CANCEL_FLAG_RX = re.compile(r"(말소|해지)")
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


EUL_RX = re.compile(r"【\s*을\s*구\s*】")
ANY_SECTION_RX = re.compile(r"【\s*(?:표\s*제\s*부|갑\s*구|을\s*구)\s*】")


def extract_mortgage_info(pdf_bytes: bytes):
    """
    【을구】 전체(여러 페이지 이어짐 포함)를 스캔:
      - '설정'만 수집
      - '말소/해지' 행은 해당 목적 텍스트에 포함된 '…번' 순위들을 취소 대상으로 마킹
    반환: {"mortgages":[...], "riskFlags":[...]}
    """
    mortgages_by_rank = {}
    cancel_ranks = set()
    risks = []

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        in_eul = False  # 을구 섹션 안에 있는지 상태 플래그

        for page in pdf.pages:
            txt = page.extract_text() or ""

            # 섹션 헤더 스위칭
            if EUL_RX.search(txt):
                in_eul = True
            elif ANY_SECTION_RX.search(txt):
                # 다른 섹션 헤더(갑구/표제부 등)를 만나면 을구 종료
                if in_eul:
                    in_eul = False
                # 을구가 아니므로 넘어감
            # 섹션 외 페이지는 스킵
            if not in_eul:
                continue

            # ---- 여기부터는 을구 섹션 안의 페이지 전부 처리 ----
            tables = page.extract_tables() or []
            for tb in tables:
                if not tb:
                    continue

                # 헤더 위치 추정 (기존 로직 유지)
                col_rank = col_purpose = col_amount = None
                for row in tb[:5]:
                    cells = [(_one_line(c) if c else "") for c in (row or [])]
                    for i, c in enumerate(cells):
                        if col_rank is None and (c in ("순위번호", "순위")):    col_rank = i
                        if col_purpose is None and ("등기" in c and "목적" in c):  col_purpose = i
                        if col_amount is None and ("채권최고액" in c):            col_amount = i
                if col_rank is None: col_rank = 0
                if col_purpose is None: col_purpose = 1
                if col_amount is None:  col_amount = 4

                for row in tb:
                    if not row or len(row) <= max(col_rank, col_purpose, col_amount):
                        continue

                    rank_raw = _one_line(row[col_rank])
                    purpose = _one_line(row[col_purpose])
                    amount_txt = _one_line(row[col_amount])

                    # 1) 말소/해지 -> 텍스트 내 '…번'들만 취소 대상으로 수집
                    if _CANCEL_FLAG_RX.search(purpose):
                        for n in _RANK_LIST_RX.findall(purpose):  # ["1","2",...]
                            cancel_ranks.add(int(n))
                        continue

                    # 2) 근저당권 '설정'만 수집
                    if ("근저당권" in purpose) and ("설정" in purpose):
                        if rank_raw.isdigit():
                            row_rank = int(rank_raw)
                            mortgages_by_rank[row_rank] = {
                                "rankNo": row_rank,
                                "amountKRW": _parse_amount_num(amount_txt),
                                "status": "normal",
                            }

                    # 위험 스캔(기존)
                    if _RISK_FLAG_RX.search(purpose):
                        risks.append({
                            "rankNo": int(rank_raw) if rank_raw.isdigit() else None,
                            "purpose": purpose
                        })

    # 말소 대상 순위를 취소 처리
    for r in cancel_ranks:
        if r in mortgages_by_rank:
            mortgages_by_rank[r]["status"] = "cancelled"

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
        words = page.extract_words(extra_attrs=["top", "text"]) or []
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
            for r in tb[header_row_idx + 1:]:
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
            addrs = _pick_addresses_from_tables(_extract_tables_on(page, crop), require_header=True,
                                                prev_last=prev_last)
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
_CO_OWNER_RX = re.compile(r"공유")


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
                    purpose = cells[1] if len(cells) > 1 else ""  # 등기목적
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


import io, re, pdfplumber


def _find_y_bottom_of(words, pattern):
    """pattern(정규식)에 매칭되는 단어들의 'bottom' 중 최댓값 반환"""
    cands = [w for w in words if re.search(pattern, w["text"])]
    return max((w["bottom"] for w in cands), default=None)


def _find_y_top_of_section_linewise(words, patterns):
    """
    words: page.extract_words() 결과
    patterns: 공백 없는 정규식 패턴 목록 (예: '갑구', '을구', '표제부', '전유부분의건물의표시', '대지권의표시')
    반환: 해당 섹션 라인의 top (없으면 None)
    """
    # 1) 같은 줄(유사 y)에 있는 word들을 묶어서 한 줄 텍스트로 합치기
    lines = defaultdict(list)
    for w in words:
        # 같은 줄 판정: top 값을 반올림해서 key로 사용 (허용 오차 2~3px 정도)
        key = round(w["top"] / 2)  # 필요하면 3,5 등으로 조절
        lines[key].append(w)

    y_candidates = []
    for key, ws in lines.items():
        # 한 줄의 텍스트를 연결
        ws_sorted = sorted(ws, key=lambda x: x["x0"])
        line_text = "".join(w["text"] for w in ws_sorted)

        # 2) 공백/괄호/특수기호 제거 후 비교
        norm = re.sub(r"[\s【】\[\]\(\)<>]", "", line_text)

        # 3) 패턴 매칭 (공백 없이 만든 패턴과 비교)
        if any(re.search(p, norm) for p in patterns):
            # 이 라인의 실제 top은 라인 내 단어들의 최소 top 사용
            y_top = min(w["top"] for w in ws_sorted)
            y_candidates.append(y_top)

    return min(y_candidates) if y_candidates else None


def _combine_address_lines(lines):
    """
    소재지번 셀 내 줄들이
      [ '1. 서울특별시 서초구 서초동', '1317-16', '2. 서울특별시 서초구 서초동', '1317-17', ... ]
    형태일 때, (행정구역 + 지번) 페어로 합쳐서 한 줄씩 반환
    """
    combined = []
    buf = None
    for s in lines:
        s = s.strip()
        if not s:
            continue
        if buf is None:
            buf = s
        else:
            combined.append((buf + " " + s).strip())
            buf = None
    if buf is not None:  # 홀수 개로 끝나면 남은 것 그대로
        combined.append(buf)
    return combined


def extract_land_share_table(pdf_bytes: bytes):
    """
    (대지권의 목적인 토지의 표시) 이후 영역만 잘라 테이블 추출
    - 페이지 내 헤더 y좌표 아래로 crop
    - 같은 페이지에 '갑구/을구'가 나오면 그 위까지만 crop
    - 소재지번 줄바꿈(행정구역/지번) 페어를 합쳐 한 줄 주소로 정규화
    """
    results = []
    in_section = False

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            words = page.extract_words(use_text_flow=True, keep_blank_chars=False)

            # 1) 섹션 시작 y 찾기 (현재 페이지에서 헤더 발견 시 그 아랫부분만)
            y0 = None
            if not in_section:
                # '대지권의' 만으로도 시작 포착 (공백 무시는 단어단위라 '\s*'보단 키워드로)
                y0 = _find_y_bottom_of(words, r"대지권")
                if y0 is not None:
                    in_section = True
                else:
                    continue  # 아직 섹션 시작 안함 → 다음 페이지로

            # 2) 섹션 종료 y 찾기 (같은 페이지에 갑구/을구가 있으면 그 위까지)
            # 종료 키워드들: 공백/괄호 제거한 형태로 대비
            end_patterns = [
                r"갑구",
                r"을구",
                r"전유부분의건물의표시",
                r"대지권의표시"
            ]
            y1 = _find_y_top_of_section_linewise(words, end_patterns)

            # 3) 크롭 박스 설정 (헤더가 이 페이지에서 시작했으면 y0 아래부터, 이어지는 페이지면 전체 상단부터)
            top = (y0 + 2) if y0 is not None else 0
            bottom = (y1 - 2) if y1 is not None else page.height
            bbox = (0, top, page.width, bottom)
            sub = page.crop(bbox)

            # 4) 테이블만 추출
            tables = sub.extract_tables()

            for table in tables:
                for row in table:
                    if not row:
                        continue
                    # None → "" 및 좌우 공백 제거
                    row = [str(c).strip() if c else "" for c in row]
                    joined = "".join(row)

                    # 헤더행 스킵 (공백/개행 불규칙 대응)
                    if re.search(r"표\s*시\s*번\s*호", joined) or re.search(r"소\s*재\s*지\s*번", joined):
                        continue

                    # 열 수 보정 (최소 4열 가정: 표시번호, 소재지번, 지목, 면적, (비고))
                    while len(row) < 5:
                        row.append("")

                    표시번호, 소재지번, 지목, 면적, 비고 = row

                    # 소재지번/지목/면적에 줄바꿈이 붙어 여러 건이 한 셀에 있을 수 있음 → 분해
                    addr_lines = 소재지번.split("\n") if 소재지번 else []
                    jimo_lines = 지목.split("\n") if 지목 else []
                    area_lines = 면적.split("\n") if 면적 else []

                    # 소재지번은 (행정구역 + 지번) 페어로 합치기
                    if len(addr_lines) >= 2:
                        addr_lines = _combine_address_lines(addr_lines)

                    # 가장 긴 길이에 맞춰 행 분해
                    max_len = max(len(addr_lines), len(jimo_lines), len(area_lines), 1)
                    for i in range(max_len):
                        results.append({
                            "표시번호": 표시번호 if i == 0 else f"{표시번호}-{i + 1}" if 표시번호 else "",
                            "소재지번": (addr_lines[i].strip() if i < len(addr_lines) else "").strip() or None,
                            "지목": (jimo_lines[i].strip() if i < len(jimo_lines) else "").strip() or None,
                            "면적": (area_lines[i].strip() if i < len(area_lines) else "").strip() or None,
                            "비고": 비고 or None
                        })

            # 5) 이 페이지에서 섹션이 끝났으면 루프 종료
            if y1 is not None:
                in_section = False
                break

    # 후처리: 완전 빈 행들 제거
    cleaned = [
        r for r in results
        if any([r.get("소재지번"), r.get("지목"), r.get("면적")])
    ]
    return cleaned


_num = r'[0-9][0-9\.,]*'  # 숫자(콤마/소수점 포함)


def _parse_ratio_pairs(cell_text: str):
    """
    입력: "102446.2분의\n1539.9454\n525165분의\n7893.912\n..."
    출력: [{"numerator":"102446.2","denominator":"1539.9454","text":"102446.2분의 1539.9454"}, ...]
    """
    if not cell_text:
        return []

    lines = [ln.strip() for ln in str(cell_text).split("\n") if ln.strip()]
    pairs = []
    pending_numer = None

    for ln in lines:
        # 1) 같은 줄에 둘 다 있는 경우
        m_both = re.search(rf'({_num})\s*분의\s*({_num})', ln)
        if m_both:
            num, den = m_both.group(1), m_both.group(2)
            pairs.append({
                "numerator": num,
                "denominator": den,
                "text": f"{num}분의 {den}"
            })
            pending_numer = None
            continue

        # 2) 분자만 있는 줄 (…분의)
        m_num_only = re.search(rf'({_num})\s*분의$', ln)
        if m_num_only:
            pending_numer = m_num_only.group(1)
            continue

        # 3) 숫자만 있는 줄 (이전 줄의 '…분의'와 결합 → 분모)
        m_num = re.fullmatch(rf'{_num}', ln)
        if m_num and pending_numer is not None:
            num, den = pending_numer, m_num.group(0)
            pairs.append({
                "numerator": num,
                "denominator": den,
                "text": f"{num}분의 {den}"
            })
            pending_numer = None
            continue

        # 4) 예외(패턴 불일치) → 그대로 텍스트로 남김
        pairs.append({"numerator": None, "denominator": None, "text": ln})

    # 끝에 분자만 남아있으면 보존
    if pending_numer is not None:
        pairs.append({"numerator": pending_numer, "denominator": None, "text": f"{pending_numer}분의"})

    # 수치형 비율(den/num) 계산 부가 필드
    for p in pairs:
        try:
            if p["numerator"] and p["denominator"]:
                p["share"] = (Decimal(p["denominator"].replace(",", "")) /
                              Decimal(p["numerator"].replace(",", "")))
            else:
                p["share"] = None
        except (InvalidOperation, ZeroDivisionError):
            p["share"] = None

    return pairs


def _num_prefix(s: str):
    """문자열 앞의 번호 추출: '2 소유권대지권' → '2'"""
    if not s: return None
    m = re.match(r'^\s*(\d+)[\.\)]?\s*', s)
    return m.group(1) if m else None


# -------------------------------------------------
# 메인: (대지권의 표시) 섹션에서 테이블 추출
# columns: 표시번호 | 대지권종류 | 대지권비율 | 등기원인 및 기타사항
# -------------------------------------------------
def extract_land_right_ratios(pdf_bytes: bytes):
    results = []
    in_section = False
    last_group_no = ""

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            words = page.extract_words(use_text_flow=True, keep_blank_chars=False) or []

            # 시작 지점 찾기
            y0 = None
            if not in_section:
                y0 = _find_y_top_of_section_linewise(words, [r"대지권의표시"])
                if y0 is not None:
                    in_section = True
                else:
                    continue

            # 종료 지점(같은 페이지에 다음 섹션이 있으면 그 위까지만)
            end_patterns = [r"갑구", r"을구"]
            y1 = _find_y_top_of_section_linewise(words, end_patterns)

            top = (y0 + 2) if y0 is not None else 0
            bottom = (y1 - 2) if y1 is not None else page.height
            sub = page.crop((0, top, page.width, bottom))

            tables = sub.extract_tables()
            for table in tables:
                for row in table:
                    if not row:
                        continue
                    # None -> "" + strip
                    row = [str(c).strip() if c else "" for c in row]
                    joined = "".join(row)

                    # 헤더 라인 스킵 (공백 무시)
                    if re.search(r"표\s*시\s*번\s*호", joined) or \
                            re.search(r"대\s*지\s*권\s*종\s*류", joined) or \
                            re.search(r"대\s*지\s*권\s*비\s*율", joined):
                        continue

                    # 열 수 보정: [표시번호, 대지권종류, 대지권비율, 등기원인및기타사항]
                    while len(row) < 4:
                        row.append("")

                    group_no, kind_cell, ratio_cell, note_cell = row[:4]

                    # 표시번호가 비어 있으면 이전 그룹 번호 유지
                    if group_no:
                        last_group_no = group_no
                    else:
                        group_no = last_group_no

                    # 칸별 줄 분해
                    kinds = [s.strip() for s in kind_cell.split("\n") if s.strip()] if kind_cell else []
                    ratios = _parse_ratio_pairs(ratio_cell)
                    notes = [s.strip() for s in note_cell.split("\n") if s.strip()] if note_cell else []

                    # 최댓길이에 맞춰 확장
                    n = max(len(kinds), len(ratios), len(notes), 1)

                    for i in range(n):
                        raw_kind = kinds[i] if i < len(kinds) else None

                        # 1) 그룹번호: 대지권종류의 앞 숫자 → 표시번호 셀 숫자 → 이전 그룹 번호
                        grp_from_kind = _num_prefix(raw_kind)
                        grp_from_cell = _num_prefix(group_no)
                        group_no_final = grp_from_kind or grp_from_cell or last_group_no
                        if group_no_final:
                            last_group_no = group_no_final  # 다음 행 대비 갱신

                        # 2) 비율
                        r = ratios[i] if i < len(ratios) else {
                            "numerator": None, "denominator": None, "text": None, "share": None
                        }

                        results.append({
                            "표시번호그룹": group_no_final,  # ← 예: "2"
                            "대지권종류": raw_kind,  # ← 예: "2 소유권대지권" (숫자 보존)
                            "대지권비율": {
                                "numerator": r["numerator"],
                                "denominator": r["denominator"],
                                "text": r["text"],
                                "share": (str(r["share"]) if r["share"] is not None else None)
                            },
                            "등기원인및기타사항": notes[i] if i < len(notes) else None
                        })
            if y1 is not None:  # 이 페이지에서 섹션 종료
                in_section = False
                break

    # 불필요한 빈 레코드 제거
    cleaned = [x for x in results if any([x.get("대지권종류"), x.get("대지권비율", {}).get("text")])]
    return cleaned


def parse_float_m2(s):
    # "229.7㎡" -> 229.7
    return float(re.sub(r"[^\d\.]", "", s))


def lot_no_from_addr(addr):
    # "1. 서울특별시 ..." -> 1
    m = re.match(r"\s*(\d+)\.", addr or "")
    return int(m.group(1)) if m else None


def compute_land_share_area(land_rows, ratio_rows):
    # land_rows: [{"소재지번": "1. ...", "면적": "229.7㎡"}, ...]
    # ratio_rows: [{"표시번호그룹":"1","대지권비율":{"share":"0.01503..."}} ...]
    area_by_lot = {}
    for r in land_rows:
        lot = lot_no_from_addr(r.get("소재지번"))
        if lot is None:
            continue
        area = parse_float_m2(r.get("면적", "0"))
        area_by_lot[lot] = area

    total = 0.0
    parts = []
    for rr in ratio_rows:
        lot = None
        # 표시번호그룹이 숫자 문자열로 들어있다고 가정
        g = rr.get("표시번호그룹")
        if g and str(g).isdigit():
            lot = int(g)
        share_str = rr.get("대지권비율", {}).get("share")
        if lot is None or not share_str:
            continue
        share = float(share_str)
        area = area_by_lot.get(lot)
        if area is None:
            continue
        part = area * share
        parts.append(part)
        total += part
    return total, parts


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
        land_share_info = extract_land_share_table(data)
        land_ratios_info = extract_land_right_ratios(data)

        total, parts = compute_land_share_area(land_share_info, land_ratios_info)
        land_share_area = round(total, 2)
        joint_info = extract_joint_collateral_addresses_follow(data)
        mortgage_info = extract_mortgage_info(data)
        print(mortgage_info)
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
        jointCollateralCurrentAddress=joint_info["currentAddress"],
        mortgageInfo=mortgage_info["mortgages"],
        mortgageRiskFlags=mortgage_info["riskFlags"],  # 가압류/압류/가처분
        gabuInfo=gabu_info,
        landShareArea=land_share_area
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
            "--disable-gpu", "--window-size=1280,860",
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

    # 기본 진입: 바로 목적지로 이동 (referer 유지)
    page.goto(root + path, referer=root, wait_until="domcontentloaded", timeout=60000)

    try:
        # ✅ 'load' 대신 'domcontentloaded'로 대기
        page.wait_for_url("**/offices**", wait_until="domcontentloaded", timeout=60000)
    except PWTimeout:
        # 보정: SPA 특성상 URL은 바뀌었는데 'load'가 안 오는 케이스 방지
        page.wait_for_load_state("domcontentloaded", timeout=30000)

    # ✅ URL만 믿지 말고, 실제 목록 컨테이너가 붙을 때까지 한 번 더 대기
    page.wait_for_selector(", ".join(LIST_SEL_CANDS), state="attached", timeout=20000)


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


@app.route("/get_base_price", methods=["POST"])
def get_base_price():
    data = request.json
    emd_name = data["emd_name"]
    bunji = data["bunji"]
    ho = data["ho"]
    target_floor = data["floor"]
    target_ho = data["target_ho"]
    target_sido = data["sidoNm"]
    target_sgg = data["sggNm"]

    with sync_playwright() as p:
        browser = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",
            headless=False,  # 서버에서는 True 권장
            locale="ko-KR",
            viewport={"width": 1280, "height": 860},
            ignore_https_errors=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run", "--no-default-browser-check",
                "--disable-dev-shm-use", "--no-sandbox",
            ],
        )
        page = browser.new_page()

        # debugger 무력화 스크립트 주입
        page.add_init_script("""
            Object.defineProperty(window, 'debugger', { get: () => undefined });
            setInterval(() => { try { delete window.debugger; } catch(e) {} }, 500);
        """)

        # ───────────── 홈택스 접속 ─────────────
        page.goto(
            "https://hometax.go.kr/websquare/websquare.html?"
            "w2xPath=/ui/pp/index_pp.xml&tmIdx=47&tm2lIdx=4712090000&tm3lIdx=4712090300"
        )

        # 법정동 버튼 클릭
        btn = wait_for_element(page, "#mf_txppWframe_btnLdCdPop")
        btn.click()
        time.sleep(0.5)

        # 행정동 입력
        emd_input_box = wait_for_element(page, "#mf_txppWframe_UTECMAAA08_wframe_inputSchNm")
        emd_input_box.fill(emd_name)

        # 조회 버튼 클릭
        btn = wait_for_element(page, "#mf_txppWframe_UTECMAAA08_wframe_trigger6")
        btn.click()
        time.sleep(1)

        # 테이블 행들 (locator 방식)
        rows = page.locator("#mf_txppWframe_UTECMAAA08_wframe_ldCdAdmDVOList_body_table tbody tr")
        row_count = rows.count()

        for i in range(row_count):
            row = rows.nth(i)
            cols = row.locator("td")
            first_col = cols.nth(0).text_content().strip()
            second_col = cols.nth(1).text_content().strip()

            if target_sido in first_col and target_sgg in second_col:
                btn = cols.nth(8).locator("button[title='선택']")
                btn.click(force=True)
                break

        # 번지 입력
        bunji_input = wait_for_element(page, "#mf_txppWframe_txtBunj")
        bunji_input.fill(bunji)

        # 호 입력
        ho_input = wait_for_element(page, "#mf_txppWframe_txtHo")
        ho_input.fill(ho)

        # 검색 버튼 클릭
        search_button = wait_for_element(page, "#mf_txppWframe_group1962")
        search_button.click()

        # 건물명 선택
        build_name_button = wait_for_element(page, "a#txtItm0")
        build_name_button.click()

        # 동 select
        dong_select_box = page.locator("#mf_txppWframe_selBldComp")
        dong_select_box.select_option(index=1)

        # 층 select
        floor_select_box = page.locator("#mf_txppWframe_selBldFlor")
        floor_select_box.select_option(label=target_floor)

        # 호 select
        ho_select_box = page.locator("#mf_txppWframe_selBldHo")
        ho_select_box.select_option(label=target_ho)

        # 상세 검색 버튼 클릭
        detail_search_button = wait_for_element(page, "#mf_txppWframe_btnSchTsv")
        detail_search_button.click()

        # 기준시가 테이블
        rows2 = page.locator("#mf_txppWframe_grdCmrcBldTsvList_body_tbody tr")
        first_row = rows2.nth(0)

        td2 = first_row.locator("td").nth(1).text_content().strip()
        td3 = first_row.locator("td").nth(2).text_content().strip()

        val2 = float(td2.replace(",", ""))
        val3 = float(td3)
        result = val2 * val3
        final_price = int(val2 // 10000 * 10000)

        # ───────────── 토지 기준시가 ─────────────
        page2 = browser.new_page()
        page2.goto("https://www.realtyprice.kr/notice/gsindividual/search.htm")

        page2.locator("#sido_list").select_option(label=target_sido)
        page2.locator("#sgg_list").select_option(label=target_sgg)
        page2.locator("#eub_list").select_option(label=emd_name)

        container = page2.locator("div.search-opt3")
        container.locator("input[name='bun1']").fill(bunji)
        container.locator("input[name='bun2']").fill(ho)

        page2.click(".search-bt input[type='image']")
        page2.wait_for_selector("#dataList tr", timeout=10000)

        first_row2 = page2.locator("#dataList tr").first
        price_text = first_row2.locator("td").nth(3).text_content().strip()
        land_price = int(re.sub(r"[^0-9]", "", price_text))

        browser.close()

    return jsonify({
        "emd_name": emd_name,
        "bunji": bunji,
        "ho": ho,
        "floor": target_floor,
        "target_ho": target_ho,
        "build_base_price": final_price,
        "land_base_price": land_price
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False, threaded=False)
