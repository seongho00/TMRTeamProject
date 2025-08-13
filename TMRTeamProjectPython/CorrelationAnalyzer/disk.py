# =========================================
# 서울 행정동 위험도 분석 + GeoJSON 병합/저장 (정리된 버전)
# - 경로: 전부 절대경로 문자열 사용
# - GeoJSON 병합: 코드 정규화(+ADSTRD_CD/adm_cd/EMD_CD 호환), 병합 통계 출력
# - KakaoMap 스타일용 색상 속성 추가(risk_color_3, risk_color_7, color)
# =========================================

import os
import json
import glob
import numpy as np
import pandas as pd
from collections import Counter

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix

import matplotlib.pyplot as plt

from PythonJPA.Send import send_to_server

# ========= 기본 설정 =========
DATA_DIR = r"C:/Users/admin/Downloads/seoul_data_merge"
OUT_DIR = r"C:/Users/admin/Downloads/out_json"  # 결과 저장 폴더(절대경로 문자열)
os.makedirs(OUT_DIR, exist_ok=True)

# 원본 행정동 GeoJSON 절대경로 (Spring 리소스 폴더 기준)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../TMRTeamProject/TMRTeamProjectPython
GEOJSON_SRC = os.path.abspath(
    os.path.join(BASE_DIR, "..", "src", "main", "resources", "static", "Seoul_emds.geojson")
)

TRAIN_QUARTERS = ['20231','20232','20233','20234','20241','20242','20243','20244']
TEST_QUARTER = '20251'

CLUSTER_FEATURES = [
    '점포_수','개업_율','폐업_률','프랜차이즈_점포_수',
    '당월_매출_금액','주중_매출_금액','주말_매출_금액',
    '남성_매출_금액','여성_매출_금액',
    '연령대_20_매출_금액','연령대_30_매출_금액','연령대_40_매출_금액',
    '총_유동인구_수','남성_유동인구_수','여성_유동인구_수',
    '총_상주인구_수','총_직장_인구_수',
    '월_평균_소득_금액','지출_총금액','음식_지출_총금액'
]

CORR_CANDIDATES = [
    '총_유동인구_수','남성_유동인구_수','여성_유동인구_수',
    '연령대_10_유동인구_수','연령대_20_유동인구_수','연령대_30_유동인구_수',
    '연령대_40_유동인구_수','연령대_50_유동인구_수','연령대_60_이상_유동인구_수',
    '시간대_유동인구_수_00~06','시간대_유동인구_수_06~11','시간대_유동인구_수_11~14',
    '시간대_유동인구_수_14~17','시간대_유동인구_수_17~21','시간대_유동인구_수_21~24',
    '요일별_유동인구_수_평일','요일별_유동인구_수_주말',
    '당월_매출_금액','주중_매출_금액','주말_매출_금액',
    '요일_매출_월요일','요일_매출_화요일','요일_매출_수요일','요일_매출_목요일',
    '요일_매출_금요일','요일_매출_토요일','요일_매출_일요일',
    '남성_매출_금액','여성_매출_금액',
    '연령대_10_매출_금액','연령대_20_매출_금액','연령대_30_매출_금액',
    '연령대_40_매출_금액','연령대_50_매출_금액','연령대_60_이상_매출_금액',
    '총_상주인구_수','남성_상주인구_수','여성_상주인구_수',
    '연령대_10_상주인구_수','연령대_20_상주인구_수','연령대_30_상주인구_수',
    '연령대_40_상주인구_수','연령대_50_상주인구_수','연령대_60_이상_상주인구_수',
    '총_가구_수',
    '월_평균_소득_금액','지출_총금액',
    '식료품_지출_금액','의류_신발_지출_금액','생활용품_지출_금액',
    '의료비_지출_금액','여가_지출_금액','문화_지출_금액',
    '점포_수','프랜차이즈_점포_수','개업_점포_수','폐업_점포_수','유사_업종_점포_수',
    '총_직장_인구_수','남성_직장_인구_수','여성_직장_인구_수',
    '연령대_10_직장_인구_수','연령대_20_직장_인구_수','연령대_30_직장_인구_수',
    '연령대_40_직장_인구_수','연령대_50_직장_인구_수','연령대_60_이상_직장_인구_수'
]

BLOCK_LIST = ['아파트','지하철','학교','관공서','병원','약국','은행','유치원','학원']
COR_TARGET = '당월_매출_금액'

RISK_WEIGHTS = {
    '폐업_률': 0.4,
    '경쟁강도': 0.2,
    '프랜차이즈비중': 0.15,
    '주중주말편차': 0.15,
    '연령의존도': 0.1
}

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False


# ========= 유틸 =========
def read_csv_safely(path):
    # CSV 인코딩 자동 처리
    try:
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='cp949')

def sanitize_columns(df, target=COR_TARGET):
    # 컬럼 공백 제거 + 타깃 중복 합치기 + 전체 중복 제거
    df = df.rename(columns=lambda x: str(x).strip())
    same = [c for c in df.columns if c == target]
    if len(same) > 1:
        tmp = df[same].apply(pd.to_numeric, errors='coerce')
        df[target] = tmp.bfill(axis=1).iloc[:, 0]
        keep = [c for c in df.columns if c not in same] + [target]
        df = df[keep]
    df = df.loc[:, ~df.columns.duplicated()].copy()
    return df

def _safe_float(x):
    try:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return None
        return float(x)
    except Exception:
        return None

def _safe_int(x):
    try:
        if x is None or (isinstance(x, float) and np.isnan(x)):
            return None
        return int(x)
    except Exception:
        return None

def _safe_str(x):
    try:
        if x is None:
            return None
        return str(x)
    except Exception:
        return None

def _normalize_code(x):
    # 행정동 코드 표준화: None/NaN -> '', '123.0' -> '123', 숫자 -> '정수문자열'
    if x is None:
        return ""
    try:
        if isinstance(x, float) and np.isnan(x):
            return ""
    except Exception:
        pass
    s = str(x).strip()
    if s == "":
        return ""
    if s.endswith(".0"):
        s = s[:-2]
    try:
        if "." in s:
            f = float(s)
            if f.is_integer():
                return str(int(f))
            return s
        int(s)
        return s
    except Exception:
        return s

def _get_feature_code(props: dict) -> str:
    # GeoJSON properties에서 코드 키를 유연하게 탐색
    for k in ("행정동_코드", "ADSTRD_CD", "adm_cd", "EMD_CD"):
        if k in props and props[k] not in (None, ""):
            return _normalize_code(props[k])
    return ""

def _get_feature_name(props: dict) -> str:
    # GeoJSON properties에서 이름 키를 유연하게 탐색(참고용)
    for k in ("행정동_명", "ADSTRD_NM", "adm_nm"):
        if k in props and props[k] not in (None, ""):
            return str(props[k])
    return ""


# ========= 데이터 로드/전처리 =========
def load_data():
    # 파일 읽기
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"CSV가 없음: {DATA_DIR}")
    dfs = []
    for f in csv_files:
        try:
            df = read_csv_safely(f)
            dfs.append(df)
        except Exception as e:
            print("읽기 실패:", f, "->", e)
    if not dfs:
        raise ValueError("읽힌 파일이 없음")

    # 전체 병합 및 정리
    df_all = pd.concat(dfs, ignore_index=True)
    df_all = sanitize_columns(df_all, target=COR_TARGET)

    # 분기 필터링
    if '기준_년분기_코드' in df_all.columns:
        df_all['기준_년분기_코드'] = df_all['기준_년분기_코드'].astype(str)
        df_train_raw = df_all[df_all['기준_년분기_코드'].isin([str(q) for q in TRAIN_QUARTERS])].copy()
        df_test_raw  = df_all[df_all['기준_년분기_코드'].astype(str) == str(TEST_QUARTER)].copy()
        if df_train_raw.empty or df_test_raw.empty:
            print(df_all['기준_년분기_코드'].value_counts().sort_index())
            raise ValueError("분기 필터 결과가 비어 있음")
    else:
        train_files = [f for f in csv_files if any(q in os.path.basename(f) for q in TRAIN_QUARTERS)]
        test_files  = [f for f in csv_files if str(TEST_QUARTER) in os.path.basename(f)]
        df_train_raw = pd.concat([read_csv_safely(f) for f in train_files], ignore_index=True)
        df_test_raw  = pd.concat([read_csv_safely(f) for f in test_files],  ignore_index=True)
        df_train_raw = sanitize_columns(df_train_raw, target=COR_TARGET)
        df_test_raw  = sanitize_columns(df_test_raw,  target=COR_TARGET)

    # 아파트 컬럼 제거
    filt = lambda cols: [c for c in cols if '아파트' not in c]
    df_train_raw = df_train_raw[filt(df_train_raw.columns)]
    df_test_raw  = df_test_raw[filt(df_test_raw.columns)]

    # 공통 컬럼만 일단 맞춤
    common_cols = [c for c in df_train_raw.columns if c in df_test_raw.columns]
    df_train = df_train_raw[common_cols].copy()
    df_test  = df_test_raw[common_cols].copy()

    if df_train.empty or df_test.empty:
        raise ValueError("공통 컬럼 기준으로 정리 후 비어 있음")

    # 테스트 원본에서 서비스 업종 정보 재부착 (순서 동일 가정)
    for c in ['서비스_업종_코드', '서비스_업종_코드_명']:
        if c in df_test_raw.columns and c not in df_test.columns:
            df_test[c] = df_test_raw.loc[df_test.index, c]

    # 디버그 출력
    print("로드 완료 - train/test shape:", df_train.shape, df_test.shape)
    if '기준_년분기_코드' in df_train.columns:
        print("train 분기:", sorted(df_train['기준_년분기_코드'].astype(str).unique())[:10])
    if '기준_년분기_코드' in df_test.columns:
        print("test 분기:", sorted(df_test['기준_년분기_코드'].astype(str).unique())[:10])

    return df_train, df_test


# ========= 모델링/파생 =========
def build_clusters(df_train, df_test):
    # 클러스터 피처 스케일링 + KMeans
    df_train = df_train.copy()
    df_test = df_test.copy()
    df_train = df_train.loc[:, ~df_train.columns.duplicated()]
    df_test = df_test.loc[:, ~df_test.columns.duplicated()]

    feats = [c for c in CLUSTER_FEATURES if (c in df_train.columns and c in df_test.columns)]
    if not feats:
        df_train['cluster'] = 0
        df_test['cluster'] = 0
        print("클러스터 피처 없음 -> cluster=0")
        return df_train, df_test

    for df in (df_train, df_test):
        df[feats] = df[feats].replace([np.inf, -np.inf], np.nan)

    Xc_tr = df_train[feats].fillna(0).values
    Xc_te = df_test[feats].fillna(0).values

    if Xc_tr.shape[0] < 2:
        df_train['cluster'] = 0
        df_test['cluster'] = 0
        print("학습 샘플 부족 -> cluster=0")
        return df_train, df_test

    scaler = StandardScaler()
    Xc_tr_scaled = scaler.fit_transform(Xc_tr)
    Xc_te_scaled = scaler.transform(Xc_te)

    km = KMeans(n_clusters=5, random_state=42, n_init=10)
    df_train['cluster'] = km.fit_predict(Xc_tr_scaled).astype(int)
    df_test['cluster'] = km.predict(Xc_te_scaled).astype(int)

    # 디버그 출력
    print("cluster 분포(train):")
    print(df_train['cluster'].value_counts(dropna=False).sort_index())
    print("cluster 분포(test):")
    print(df_test['cluster'].value_counts(dropna=False).sort_index())

    return df_train, df_test

def add_risk_components(df):
    # 위험도 구성요소 파생
    df = df.copy()

    # 경쟁강도: 유사업종 점포수 (비율이 아닌 절대 수)
    if '유사_업종_점포_수' in df.columns:
        df['경쟁강도'] = df['유사_업종_점포_수'].fillna(0)
    else:
        df['경쟁강도'] = 0

    # 프랜차이즈 비중: 프랜차이즈_점포_수 / 점포_수
    if all(c in df.columns for c in ['프랜차이즈_점포_수','점포_수']):
        denom = df['점포_수'].replace(0, np.nan)
        df['프랜차이즈비중'] = (df['프랜차이즈_점포_수'] / denom).fillna(0)
    else:
        df['프랜차이즈비중'] = 0

    # 주중/주말 매출 편차 비율: |주중-주말| / 당월
    if all(c in df.columns for c in ['주중_매출_금액','주말_매출_금액','당월_매출_금액']):
        diff = (df['주중_매출_금액'] - df['주말_매출_금액']).abs()
        denom = df['당월_매출_금액'].replace(0, np.nan)
        df['주중주말편차'] = (diff / denom).fillna(0)
    else:
        df['주중주말편차'] = 0

    # 연령 의존도: (20+30+40 매출) / 당월
    if all(c in df.columns for c in ['연령대_20_매출_금액','연령대_30_매출_금액','연령대_40_매출_금액','당월_매출_금액']):
        core = df['연령대_20_매출_금액'] + df['연령대_30_매출_금액'] + df['연령대_40_매출_금액']
        denom = df['당월_매출_금액'].replace(0, np.nan)
        df['연령의존도'] = (core / denom).fillna(0)
    else:
        df['연령의존도'] = 0

    # 폐업률 없으면 0
    if '폐업_률' not in df.columns:
        df['폐업_률'] = 0

    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)
    return df

def risk_score_and_label(df_train, df_test, weights=RISK_WEIGHTS):
    # 위험도 가중합 점수 + 3단계/7단계 라벨
    scaler = StandardScaler()
    cols = [c for c in weights.keys() if c in df_train.columns]

    Z_tr = pd.DataFrame(scaler.fit_transform(df_train[cols]), columns=cols, index=df_train.index)
    Z_te = pd.DataFrame(scaler.transform(df_test[cols]), columns=cols, index=df_test.index)

    w = np.array([weights[c] for c in cols])
    df_train['위험도_점수'] = Z_tr.values @ w
    df_test['위험도_점수'] = Z_te.values @ w

    # 3분위수 기준 3단계
    qs = df_train['위험도_점수'].quantile([0, 1/3, 2/3, 1]).values
    bins = np.unique(qs).tolist()
    if len(bins) < 4:
        bins = df_train['위험도_점수'].quantile([0, 1/3, 2/3, 1]).tolist()

    df_train['위험도'] = pd.cut(df_train['위험도_점수'], bins=bins, labels=[0,1,2], include_lowest=True, duplicates='drop').astype(int)
    df_test['위험도'] = pd.cut(df_test['위험도_점수'], bins=bins, labels=[0,1,2], include_lowest=True, duplicates='drop')
    df_test = df_test[df_test['위험도'].notna()].copy()
    df_test['위험도'] = df_test['위험도'].astype(int)

    # 7분위수 기준 7단계
    q7 = df_train['위험도_점수'].quantile([i/7 for i in range(8)]).values.tolist()
    q7 = sorted(set(q7))
    if len(q7) < 8:
        base = [i/7 for i in range(8)]
        mn, mx = float(df_train['위험도_점수'].min()), float(df_train['위험도_점수'].max())
        q7 = sorted(set([mn + (mx-mn)*b for b in base]))
    labels7 = ['1단계','2단계','3단계','4단계','5단계','6단계','7단계']
    df_train['위험도7'] = pd.cut(df_train['위험도_점수'], bins=q7, labels=labels7[:len(q7)-1], include_lowest=True, duplicates='drop')
    df_test['위험도7'] = pd.cut(df_test['위험도_점수'], bins=q7, labels=labels7[:len(q7)-1], include_lowest=True, duplicates='drop')

    # 디버그 출력
    print("위험도_점수 통계(train):")
    print(df_train['위험도_점수'].describe())
    print("위험도 3단계 분포(train):", df_train['위험도'].value_counts().sort_index().to_dict())
    print("위험도 7단계 분포(train):")
    print(df_train['위험도7'].value_counts().sort_index())

    return df_train, df_test

def top_corr_features(df, k=20):
    # 타깃과의 상관계수 상위 k개 피처 반환
    df = sanitize_columns(df, target=COR_TARGET)
    if COR_TARGET in df.columns:
        df[COR_TARGET] = pd.to_numeric(df[COR_TARGET], errors='coerce')

    cand = [c for c in CORR_CANDIDATES if c in df.columns and not any(b in c for b in BLOCK_LIST) and c != COR_TARGET]
    valid = list(dict.fromkeys(cand + [COR_TARGET]))

    sub = df[valid].loc[:, ~df[valid].columns.duplicated()].copy()
    if COR_TARGET not in sub.columns:
        return cand[:k]

    cor = sub.corr(numeric_only=True)
    if COR_TARGET not in cor.columns:
        return cand[:k]

    order = (
        cor[COR_TARGET]
        .drop(labels=[COR_TARGET], errors='ignore')
        .sort_values(ascending=False)
        .head(k)
        .index.tolist()
    )

    # 디버그 출력
    print("상위 상관 피처:", order[:10])
    print("상관계수 상위 5개 미니 테이블:")
    print(cor[[COR_TARGET]].sort_values(by=COR_TARGET, ascending=False).head(6))

    return order


# ========= GeoJSON 병합/저장 =========
COLOR_3 = {0: "#9AD1A3", 1: "#FFD480", 2: "#FF8A80"}  # 3단계 색
COLOR_7 = {"1단계":"#e8f5e9","2단계":"#c8e6c9","3단계":"#a5d6a7","4단계":"#81c784","5단계":"#66bb6a","6단계":"#ffb74d","7단계":"#e57373"}

def save_result_as_geojson(
        src_geojson_path: str,
        out_geojson_path: str,
        df_result: pd.DataFrame,
        code_col: str = "행정동_코드",
        name_col: str = "행정동_코드_명"
):
    # 경로/입력 검증
    if not os.path.exists(src_geojson_path):
        raise FileNotFoundError(f"원본 GeoJSON이 없음: {src_geojson_path}")
    out_dir = os.path.dirname(out_geojson_path)
    os.makedirs(out_dir, exist_ok=True)

    # DF -> dict 매핑(정규화 코드 키)
    key_map = {}
    for _, row in df_result.iterrows():
        key = _normalize_code(row.get(code_col, ""))
        if not key:
            continue
        key_map[key] = {
            "행정동_코드": key,
            "행정동_코드_명": row.get(name_col, None),
            "서비스_업종_코드": row.get("서비스_업종_코드", None),
            "서비스_업종_코드_명": row.get("서비스_업종_코드_명", None),
            "위험도_점수": _safe_float(row.get("위험도_점수")),
            "위험도": _safe_int(row.get("위험도")),
            "위험도7": _safe_str(row.get("위험도7")),
            "예측_위험도": _safe_int(row.get("예측_위험도"))
        }

    # GeoJSON 로드
    with open(src_geojson_path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    # feature 순회하며 속성 병합
    feats = gj.get("features", [])
    matched = 0
    for feat in feats:
        props = feat.get("properties", {}) or {}
        code = _get_feature_code(props)
        if not code:
            # 코드 키 자체가 없거나 값이 비정상
            continue

        r = key_map.get(code)
        if not r:
            # 데이터가 없으면 표시만 기본값으로
            props.setdefault("risk_exists", False)
            props.setdefault("risk_color_3", "#D3D3D3")
            props.setdefault("risk_color_7", "#D3D3D3")
            feat["properties"] = props
            continue

        # 위험도/점수/업종 등 값 병합
        matched += 1
        props["risk_exists"] = True
        props["행정동_코드"] = r["행정동_코드"]

        # 이름: DF에 있으면 '행정동_명'에 기록(GeoJSON의 ADSTRD_NM 등은 그대로 둠)
        if r.get("행정동_코드_명") is not None:
            props["행정동_명"] = r["행정동_코드_명"]

        # 업종 정보
        if r.get("서비스_업종_코드") is not None:
            props["서비스_업종_코드"] = r["서비스_업종_코드"]
        if r.get("서비스_업종_코드_명") is not None:
            props["서비스_업종_코드_명"] = r["서비스_업종_코드_명"]

        # 위험도 결과
        props["위험도_점수"] = r["위험도_점수"]
        props["위험도"] = r["위험도"]
        props["위험도7"] = r["위험도7"]
        props["예측_위험도"] = r["예측_위험도"]

        # 색상 프로퍼티 추가(지금 당장 KakaoMap 스타일에 활용 가능)
        props["risk_color_3"] = COLOR_3.get(r["위험도"], "#D3D3D3")
        props["risk_color_7"] = COLOR_7.get(r["위험도7"], "#D3D3D3")
        props["color"] = props["risk_color_3"]

        feat["properties"] = props

    gj["features"] = feats

    # 저장 (한글 유지를 위해 ensure_ascii=False)
    with open(out_geojson_path, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)

    # 매칭 통계 출력
    print(f"[GeoJSON 병합] features: {len(feats)}, 매칭 성공: {matched}, 매칭 실패: {len(feats) - matched}")


# ========= 학습/평가/저장 =========
def train_and_eval(df_train, df_test):
    # 피처 선택
    top_feats = top_corr_features(df_train, k=20)
    feature_cols = list(dict.fromkeys(top_feats + ['cluster']))

    X_tr = df_train[feature_cols].fillna(0)
    y_tr = df_train['위험도']
    X_te = df_test[feature_cols].fillna(0)
    y_te = df_test['위험도']

    print("학습/평가 입력 크기:", X_tr.shape, X_te.shape)
    print("레이블 분포(train/test):", Counter(y_tr), Counter(y_te))

    # 모델 학습
    rf = RandomForestClassifier(
        n_estimators=500,
        random_state=42,
        n_jobs=-1,
        class_weight='balanced'
    )
    rf.fit(X_tr, y_tr)

    # 예측 및 평가
    y_pred = rf.predict(X_te)
    print("혼동행렬:")
    print(confusion_matrix(y_te, y_pred))
    print("분류리포트:")
    print(classification_report(y_te, y_pred, zero_division=0))

    # 변수 중요도
    importances = pd.Series(rf.feature_importances_, index=feature_cols).sort_values(ascending=False)
    print("변수 중요도 TOP10:")
    print(importances.head(10))
    plt.figure(figsize=(10,7))
    importances.sort_values(ascending=True).plot(kind='barh')
    plt.title('위험도 예측 변수 중요도')
    plt.tight_layout()
    plt.show()

    # 결과 저장
    code_cols = [c for c in ['행정동_코드','행정동_코드_명'] if c in df_test.columns]
    extra_cols = [c for c in ['서비스_업종_코드', '서비스_업종_코드_명'] if c in df_test.columns]
    exist_cols = code_cols + extra_cols + ['위험도_점수','위험도','위험도7']

    if code_cols:
        out = df_test[exist_cols].copy()
        out['예측_위험도'] = y_pred
        print(out.head(3))

        try:
            print(out.columns)
            send_to_server(out)
        except Exception as e:
            print(e)

        # GeoJSON 저장 호출
        out_geojson_path = os.path.abspath(
            os.path.join(BASE_DIR, "..", "src", "main", "resources", "static", "Seoul_risk.geojson")
        )
        try:
            save_result_as_geojson(
                src_geojson_path=GEOJSON_SRC,
                out_geojson_path=out_geojson_path,
                df_result=out,
                code_col="행정동_코드",
                name_col="행정동_코드_명",
            )
            print(f"GeoJSON 저장 완료: {out_geojson_path}")
        except Exception as e:
            print("GeoJSON 저장 실패:", e)

# ========= 메인 =========
def main():
    # 로드
    df_train, df_test = load_data()

    # 클러스터
    df_train, df_test = build_clusters(df_train, df_test)

    # 위험 요소 파생
    df_train = add_risk_components(df_train)
    df_test = add_risk_components(df_test)
    print("파생 컬럼 확인(일부):", [c for c in ['경쟁강도','프랜차이즈비중','주중주말편차','연령의존도','폐업_률'] if c in df_train.columns])

    # 위험 점수/라벨
    df_train, df_test = risk_score_and_label(df_train, df_test, weights=RISK_WEIGHTS)

    # 학습/평가/저장
    train_and_eval(df_train, df_test)

if __name__ == "__main__":
    main()
