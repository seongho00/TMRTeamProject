import json
import os
import numpy as np
import pandas as pd
from collections import Counter

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils import compute_class_weight
from tqdm import tqdm

from PythonJPA.Send import send_to_server

# 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "..", "src", "main", "resources", "seoul_data_merge")
)

TRAIN_FILES = [
    "서울_데이터_병합_20221.csv",
    "서울_데이터_병합_20222.csv",
    "서울_데이터_병합_20223.csv",
    "서울_데이터_병합_20224.csv",
    "서울_데이터_병합_20231.csv",
    "서울_데이터_병합_20232.csv",
    "서울_데이터_병합_20233.csv",
    "서울_데이터_병합_20234.csv",
    "서울_데이터_병합_20241.csv",
    "서울_데이터_병합_20242.csv",
    "서울_데이터_병합_20243.csv",
    "서울_데이터_병합_20244.csv"
]
TEST_FILE = "서울_데이터_병합_20251.csv"

# 변수 목록
selected_features = [
    '점포_수', '개업_율', '폐업_률', '프랜차이즈_점포_수',
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_20_매출_금액', '연령대_30_매출_금액', '연령대_40_매출_금액',
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '총_상주인구_수', '총_직장_인구_수',
    '월_평균_소득_금액', '지출_총금액', '음식_지출_총금액',
    '지하철_역_수', '대학교_수', '관공서_수'
]

correlation_features = [
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '연령대_10_유동인구_수', '연령대_20_유동인구_수', '연령대_30_유동인구_수',
    '연령대_40_유동인구_수', '연령대_50_유동인구_수', '연령대_60_이상_유동인구_수',
    '시간대_유동인구_수_00~06', '시간대_유동인구_수_06~11', '시간대_유동인구_수_11~14',
    '시간대_유동인구_수_14~17', '시간대_유동인구_수_17~21', '시간대_유동인구_수_21~24',
    '요일별_유동인구_수_평일', '요일별_유동인구_수_주말',
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '요일_매출_월요일', '요일_매출_화요일', '요일_매출_수요일', '요일_매출_목요일',
    '요일_매출_금요일', '요일_매출_토요일', '요일_매출_일요일',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_10_매출_금액', '연령대_20_매출_금액', '연령대_30_매출_금액',
    '연령대_40_매출_금액', '연령대_50_매출_금액', '연령대_60_이상_매출_금액',
    '총_상주인구_수', '남성_상주인구_수', '여성_상주인구_수',
    '연령대_10_상주인구_수', '연령대_20_상주인구_수', '연령대_30_상주인구_수',
    '연령대_40_상주인구_수', '연령대_50_상주인구_수', '연령대_60_이상_상주인구_수',
    '총_가구_수',
    '월_평균_소득_금액', '지출_총금액',
    '식료품_지출_금액', '의류_신발_지출_금액', '생활용품_지출_금액',
    '의료비_지출_금액', '여가_지출_금액', '문화_지출_금액',
    '점포_수', '프랜차이즈_점포_수', '개업_점포_수', '폐업_점포_수', '유사_업종_점포_수',
    '총_직장_인구_수', '남성_직장_인구_수', '여성_직장_인구_수',
    '연령대_10_직장_인구_수', '연령대_20_직장_인구_수', '연령대_30_직장_인구_수',
    '연령대_40_직장_인구_수', '연령대_50_직장_인구_수', '연령대_60_이상_직장_인구_수'
]

# 위험도 구성요소 가중치(필요시 조정)
RISK_WEIGHTS = {
    '경쟁강도': 0.20,        # 유사_업종_점포_수
    '프랜차이즈비중': 0.15,  # 프랜차이즈_점포_수 / 점포_수
    '주중주말편차': 0.25,    # |주중 - 주말| / 당월
    '연령의존도': 0.10,      # (20+30+40 매출) / 당월
    '폐업_률': 0.30          # 폐업_률 자체
}

# 식별/그룹 기준 컬럼 후보
ID_COLS = ['행정동_코드', '행정동_코드_명', '서비스_업종_코드', '서비스_업종_코드_명']

# 유틸 함수
def read_csv_any(path):
    # UTF-8 우선, 실패 시 CP949 시도
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp949")

def unify_columns(df: pd.DataFrame) -> pd.DataFrame:
    # 컬럼 문자열화 및 공백 제거, 중복 제거
    df = df.rename(columns=lambda c: str(c).strip())
    df = df.loc[:, ~df.columns.duplicated()].copy()
    return df

def ensure_numeric(df: pd.DataFrame, cols):
    # 지정 컬럼을 숫자로 강제 변환
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def add_cluster_features(df_train, df_test, feats, n_clusters=5, random_state=42):
    # 군집 변수 없으면 cluster=0 지정
    feats = [c for c in feats if c in df_train.columns and c in df_test.columns]
    if not feats:
        df_train['cluster'] = 0
        df_test['cluster'] = 0
        return df_train, df_test

    # 결측/무한 처리
    for d in (df_train, df_test):
        d[feats] = d[feats].replace([np.inf, -np.inf], np.nan).fillna(0)

    scaler = StandardScaler()
    Xtr = scaler.fit_transform(df_train[feats].values)
    Xte = scaler.transform(df_test[feats].values)

    if Xtr.shape[0] < n_clusters:
        # 표본이 적으면 단일 클러스터
        df_train['cluster'] = 0
        df_test['cluster'] = 0
        return df_train, df_test

    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df_train['cluster'] = km.fit_predict(Xtr)
    df_test['cluster'] = km.predict(Xte)
    return df_train, df_test

def add_risk_components(df):
    # 위험도 구성요소 파생
    df = df.copy()

    # 경쟁강도: 유사업종 점포수
    if '유사_업종_점포_수' in df.columns:
        df['경쟁강도'] = df['유사_업종_점포_수'].fillna(0)
    else:
        df['경쟁강도'] = 0

    # 프랜차이즈비중: 프랜차이즈_점포_수 / 점포_수
    if all(c in df.columns for c in ['프랜차이즈_점포_수', '점포_수']):
        denom = df['점포_수'].replace(0, np.nan)
        df['프랜차이즈비중'] = (df['프랜차이즈_점포_수'] / denom).fillna(0)
    else:
        df['프랜차이즈비중'] = 0

    # 주중주말편차: |주중 - 주말| / 당월
    if all(c in df.columns for c in ['주중_매출_금액', '주말_매출_금액', '당월_매출_금액']):
        diff = (df['주중_매출_금액'] - df['주말_매출_금액']).abs()
        denom = df['당월_매출_금액'].replace(0, np.nan)
        df['주중주말편차'] = (diff / denom).fillna(0)
    else:
        df['주중주말편차'] = 0

    # 연령의존도: (20+30+40 매출)/당월
    if all(c in df.columns for c in ['연령대_20_매출_금액','연령대_30_매출_금액','연령대_40_매출_금액','당월_매출_금액']):
        core = df['연령대_20_매출_금액'] + df['연령대_30_매출_금액'] + df['연령대_40_매출_금액']
        denom = df['당월_매출_금액'].replace(0, np.nan)
        df['연령의존도'] = (core / denom).fillna(0)
    else:
        df['연령의존도'] = 0

    # 폐업_률 없으면 0
    if '폐업_률' not in df.columns:
        df['폐업_률'] = 0

    # 정리
    df = df.replace([np.inf, -np.inf], 0).fillna(0)
    return df

def risk_score_label(train_df, test_df, weights=RISK_WEIGHTS):
    # 표준화 후 가중합 점수 계산
    cols = [c for c in weights.keys() if c in train_df.columns]
    if not cols:
        train_df['위험도_점수'] = 0
        test_df['위험도_점수'] = 0
    else:
        scaler = StandardScaler()
        Ztr = scaler.fit_transform(train_df[cols].values)
        Zte = scaler.transform(test_df[cols].values)
        w = np.array([weights[c] for c in cols])
        train_df['위험도_점수'] = Ztr @ w
        test_df['위험도_점수'] = Zte @ w

    # 5분위 경계 계산
    qs = train_df['위험도_점수'].quantile([i/5 for i in range(6)]).values
    bins = np.unique(qs).tolist()
    if len(bins) < 6:
        mn, mx = float(train_df['위험도_점수'].min()), float(train_df['위험도_점수'].max())
        if mn == mx:
            mn, mx = mn - 1e-6, mx + 1e-6
        bins = [mn + (mx - mn) * i / 5 for i in range(6)]

    # 1) 학습용 숫자 라벨(0~4)
    num_labels = [0, 1, 2, 3, 4]
    train_df['위험도'] = pd.cut(train_df['위험도_점수'], bins=bins, labels=num_labels, include_lowest=True).astype(int)
    test_df['위험도']  = pd.cut(test_df['위험도_점수'],  bins=bins, labels=num_labels, include_lowest=True)
    test_df = test_df[test_df['위험도'].notna()].copy()
    test_df['위험도'] = test_df['위험도'].astype(int)

    # 2) 보기용 문자열 라벨(별도 컬럼)
    label_map = {
        0: '매우 낮음',
        1: '낮음',
        2: '보통',
        3: '높음',
        4: '매우 높음'
    }
    train_df['위험도_라벨'] = train_df['위험도'].map(label_map)
    test_df['위험도_라벨']  = test_df['위험도'].map(label_map)

    # 참고용 5단계 라벨
    q5 = np.quantile(train_df['위험도_점수'], [i/5 for i in range(6)])
    q5 = sorted(set(q5))
    if len(q5) < 6:
        mn, mx = float(train_df['위험도_점수'].min()), float(train_df['위험도_점수'].max())
        q5 = [mn + (mx - mn) * i / 5 for i in range(6)]
    labels5 = ['1단계', '2단계', '3단계', '4단계', '5단계']
    train_df['위험도_단계'] = pd.cut(train_df['위험도_점수'], bins=q5, labels=labels5[:len(q5)-1], include_lowest=True)
    test_df['위험도_단계'] = pd.cut(test_df['위험도_점수'], bins=q5, labels=labels5[:len(q5)-1], include_lowest=True)

    return train_df, test_df

def corr_analysis(df: pd.DataFrame, target='당월_매출_금액', features=None, out_path=None, top_k=30):
    # 상관분석: target과의 피어슨 상관계수 상위 top_k
    cols = [c for c in (features or []) if c in df.columns] + [target]
    cols = list(dict.fromkeys(cols))
    sub = df[cols].copy()
    sub = ensure_numeric(sub, cols)
    cor = sub.corr(numeric_only=True)
    if target not in cor.columns:
        return []
    ranking = (
        cor[target]
        .drop(labels=[target], errors='ignore')
        .sort_values(ascending=False)
        .dropna()
        .head(top_k)
    )
    if out_path:
        ranking.to_csv(out_path, encoding="utf-8-sig")
    return ranking.index.tolist()

# 데이터 로드
train_list = []
for fn in TRAIN_FILES:
    path = os.path.join(DATA_DIR, fn)
    if os.path.exists(path):
        df = read_csv_any(path)
        train_list.append(df)
if not train_list:
    raise FileNotFoundError("학습용 CSV(20221~20244)가 없습니다.")

test_path = os.path.join(DATA_DIR, TEST_FILE)
if not os.path.exists(test_path):
    raise FileNotFoundError("테스트 CSV(20251)가 없습니다.")
df_test_raw = read_csv_any(test_path)

df_train_raw = pd.concat(train_list, ignore_index=True)

# 컬럼 정리
df_train_raw = unify_columns(df_train_raw)
df_test_raw  = unify_columns(df_test_raw)

# 식별자 보존
keep_ids = [c for c in ID_COLS if c in df_test_raw.columns]
if not keep_ids:
    # 최소한 행정동/업종명이 있어야 함
    raise ValueError("테스트 데이터에 식별 컬럼(행정동/업종)이 없습니다.")

# 군집분석 피처 추가
df_train_clu = df_train_raw.copy()
df_test_clu  = df_test_raw.copy()

df_train_clu, df_test_clu = add_cluster_features(
    df_train_clu, df_test_clu, selected_features, n_clusters=5, random_state=42
)

# 위험도 구성요소 파생 + 점수/라벨 생성
df_train_feat = add_risk_components(df_train_clu)
df_test_feat  = add_risk_components(df_test_clu)

df_train_feat, df_test_feat = risk_score_label(df_train_feat, df_test_feat, weights=RISK_WEIGHTS)

# 상관분석 (타깃: 당월_매출_금액)
top_corr = corr_analysis(
    df_train_feat,
    target='당월_매출_금액',
    features=correlation_features,
    top_k=30
)

# 랜덤포레스트 학습/예측 (타깃: 위험도)
# 입력 피처: 상관 상위 + cluster + 주요 파생
base_features = list(top_corr) + ['cluster', '경쟁강도', '프랜차이즈비중', '주중주말편차', '연령의존도', '폐업_률']
base_features = [c for c in base_features if c in df_train_feat.columns and c in df_test_feat.columns]

X_tr = df_train_feat[base_features].replace([np.inf, -np.inf], 0).fillna(0)
y_tr = df_train_feat['위험도'].astype(int)

X_te = df_test_feat[base_features].replace([np.inf, -np.inf], 0).fillna(0)
y_te = df_test_feat['위험도'].astype(int)  # 테스트도 라벨 존재(비교/평가용)

class RFwithProgress(RandomForestClassifier):
    def fit(self, X, y, **kwargs):
        # 전체 트리 개수
        n_estimators = self.n_estimators

        with tqdm(total=n_estimators, unit="tree") as pbar:
            self.set_params(warm_start=True)
            for i in range(1, n_estimators + 1):
                self.set_params(n_estimators=i)
                super(RandomForestClassifier, self).fit(X, y, **kwargs)
                pbar.update(1)

        return self

# y_tr은 학습용 타겟 데이터
classes = np.unique(y_tr)
weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_tr)
class_weights_dict = dict(zip(classes, weights))

rf = RFwithProgress(
    n_estimators=600,
    random_state=42,
    n_jobs=-1,
    class_weight=class_weights_dict
)
rf.fit(X_tr, y_tr)
pred = rf.predict(X_te)
proba = rf.predict_proba(X_te) if hasattr(rf, "predict_proba") else None

# 평가 리포트 출력
print("=== 입력 크기 ===")
print("X_tr:", X_tr.shape, "X_te:", X_te.shape)
print("레이블 분포 train/test:", Counter(y_tr), Counter(y_te))
print("\n=== 혼동행렬 ===")
print(confusion_matrix(y_te, pred))
print("\n=== 분류 리포트 ===")
print(classification_report(y_te, pred, zero_division=0))

# 중요도 상위 20
fi = pd.Series(rf.feature_importances_, index=base_features).sort_values(ascending=False)
print("\n=== 변수 중요도 TOP 20 ===")
print(fi.head(20))

# 결과 저장 (20251 예측)
out_cols = [c for c in keep_ids if c in df_test_raw.columns]
out = df_test_raw[out_cols].copy()

# 실제/예측 라벨 및 점수
out['실제_위험도'] = y_te.values
out['예측_위험도'] = pred
out['위험도_점수'] = df_test_feat.loc[X_te.index, '위험도_점수'].values
out['위험도_단계'] = df_test_feat.loc[X_te.index, '위험도_단계'].astype(str).values

# 예측 신뢰도(최대 확률) 추가
if proba is not None:
    out['예측_신뢰도'] = proba.max(axis=1)
else:
    out['예측_신뢰도'] = np.nan

# 정렬(선택)
pref = ['행정동_코드','행정동_코드_명','서비스_업종_코드','서비스_업종_코드_명','실제_위험도','예측_위험도','예측_신뢰도','위험도_점수','위험도_단계']
ordered = [c for c in pref if c in out.columns] + [c for c in out.columns if c not in pref]
out = out[ordered]


# 위험도 점수 정규화 (퍼센타일 방식, 0~100)
df = out.copy()  # 원본 보존용 복사본

# 전체 퍼센타일 스케일 (0 ~ 100)
# 0~100 범위로 변환
df["risk100_all"] = (df["위험도_점수"].rank(pct=True, method="average") * 100).round(1)

# 업종별 퍼센타일 스케일
# 같은 업종 안에서만 상대적인 순위(0~100)를 부여
df["risk100_by_biz"] = (df.groupby("서비스_업종_코드")["위험도_점수"].transform(lambda g: g.rank(pct=True, method="average") * 100)).round(1)

print("\n=== 결과 상위 10행 ===")
print(df.head(10))

# DB 저장
try:
    print(df.columns)
    send_to_server(df)
    print("DB 저장 완료")
except Exception as e:
    print(e)

# 분포 확인 (0~100 고르게 펴졌는지 체크)
print("risk100_all 통계:\n", df["risk100_all"].describe())
print("고유 값 개수:", df["risk100_all"].nunique())

# 퍼센타일 계산 이후
out = df

# 5단계 팔레트(낮음→높음)
PALETTE_5 = {
    0: "#E3F2FD",  # 매우 낮음
    1: "#BBDEFB",  # 낮음
    2: "#90CAF9",  # 보통
    3: "#64B5F6",  # 높음
    4: "#1E88E5",  # 매우 높음
}
LABEL_5 = {0: "매우 낮음", 1: "낮음", 2: "보통", 3: "높음", 4: "매우 높음"}

# GeoJSON 원본/출력 경로 (프로젝트 구조에 맞게 조정)
GEOJSON_SRC = os.path.abspath(
    os.path.join(BASE_DIR, "..", "src", "main", "resources", "static", "Seoul_emds.geojson")
)
GEOJSON_OUT = os.path.abspath(
    os.path.join(BASE_DIR, "..", "src", "main", "resources", "static", "Seoul_risk.geojson")
)

def _normalize_code(x):
    """행정동 코드 표준화: None/NaN → '', '123.0' → '123'"""
    if x is None:
        return ""
    try:
        if isinstance(x, float) and np.isnan(x):
            return ""
    except Exception:
        pass
    s = str(x).strip()
    if not s:
        return ""
    if s.endswith(".0"):
        s = s[:-2]
    try:
        if "." in s:
            f = float(s)
            return str(int(f)) if f.is_integer() else s
        int(s)
        return s
    except Exception:
        return s

def _get_feature_code(props: dict) -> str:
    """GeoJSON properties 안에서 행정동 코드를 유연하게 추출"""
    for k in ("행정동_코드", "ADSTRD_CD", "adm_cd", "EMD_CD"):
        if k in props and props[k] not in (None, ""):
            return _normalize_code(props[k])
    return ""

def _get_feature_name(props: dict) -> str:
    """GeoJSON properties 안에서 행정동 이름을 유연하게 추출(참고용)"""
    for k in ("행정동_코드_명", "행정동_명", "ADSTRD_NM", "adm_nm"):
        if k in props and props[k] not in (None, ""):
            return str(props[k])
    return ""

def _build_service_list(df_group: pd.DataFrame) -> list:
    """동 내부 업종별 위험도 리스트 생성(아이템별 color 계산)"""
    items = []
    for _, r in df_group.iterrows():
        # 색상 계산: 예측_위험도(0~4) 우선, 없으면 위험도_단계('1단계'~'5단계') 사용
        color = "#D3D3D3"
        try:
            if pd.notna(r.get("예측_위험도")):
                color = PALETTE_5.get(int(r["예측_위험도"]), "#D3D3D3")
            elif pd.notna(r.get("위험도_단계")):
                step = str(r["위험도_단계"]).replace("단계", "")
                idx = max(0, min(4, int(step) - 1))
                color = PALETTE_5.get(idx, "#D3D3D3")
        except Exception:
            # 변환 실패 시 기본 회색 유지
            pass

        # 업종별 상세 정보 구성
        item = {
            "서비스_업종_코드": r.get("서비스_업종_코드"),
            "서비스_업종_코드_명": r.get("서비스_업종_코드_명"),
            "예측_위험도": int(r["예측_위험도"]) if pd.notna(r.get("예측_위험도")) else None,
            "예측_위험도_라벨": LABEL_5.get(int(r["예측_위험도"]), None) if pd.notna(r.get("예측_위험도")) else None,
            "예측_신뢰도": float(r["예측_신뢰도"]) if pd.notna(r.get("예측_신뢰도")) else None,
            "위험도_점수": float(r["risk100_all"]) if pd.notna(r.get("risk100_all")) else None,
            "위험도_업종별_점수": float(r["risk100_by_biz"]) if pd.notna(r.get("risk100_by_biz")) else None,
            "위험도_단계": r.get("위험도_단계"),
            "color": color,
        }
        items.append(item)

    # 업종명 사전순 정렬 (필요 시 위험도 내림차순 정렬로 변경 가능)
    items.sort(key=lambda x: (x["서비스_업종_코드_명"] or ""))
    return items

def _coerce_numeric_cols(df: pd.DataFrame, cols, ndigits=None):
    for c in cols:
        if c not in df.columns:
            print(f"[WARN] 컬럼 없음: {c}")
            df[c] = np.nan
        df[c] = pd.to_numeric(df[c], errors="coerce")
        if ndigits is not None:
            df[c] = df[c].round(ndigits)
    # 진단 출력
    print(df[cols].describe(include="all"))
    print("NaN 비율:", df[cols].isna().mean().to_dict())

def save_result_as_geojson(src_geojson_path: str, out_geojson_path: str, df_result: pd.DataFrame):
    # 경로 체크
    if not os.path.exists(src_geojson_path):
        raise FileNotFoundError(f"원본 GeoJSON이 없음: {src_geojson_path}")
    os.makedirs(os.path.dirname(out_geojson_path), exist_ok=True)

    # 필요한 컬럼 확인
    if "행정동_코드" not in df_result.columns:
        raise KeyError("df_result에 '행정동_코드' 컬럼이 필요해")
    if "행정동_코드_명" not in df_result.columns:
        df_result["행정동_코드_명"] = None

    # 동 단위 그룹핑 → 업종 리스트 빌드
    dong_map = {}
    for (emd_cd, emd_nm), g in df_result.groupby(["행정동_코드", "행정동_코드_명"], dropna=False):
        emd_cd_norm = _normalize_code(emd_cd)
        services = _build_service_list(g)
        dong_map[emd_cd_norm] = {
            "행정동_코드": emd_cd_norm,
            "행정동_코드_명": emd_nm,
            "업종별_위험도": services,
            "업종_개수": len(services),
        }

    # GeoJSON 로드
    with open(src_geojson_path, "r", encoding="utf-8") as f:
        gj = json.load(f)

    feats = gj.get("features", [])
    matched = 0

    for feat in feats:
        props = feat.get("properties", {}) or {}

        # 기존 대표/색상 필드 깔끔히 제거
        for k in ["대표_예측_위험도", "대표_예측_라벨", "risk_color_5", "color"]:
            if k in props:
                props.pop(k, None)

        # 행정동 코드 획득
        code = _get_feature_code(props)
        if not code:
            # 코드 없으면 비매칭 처리
            props["risk_exists"] = False
            props["업종별_위험도"] = []
            props["업종_개수"] = 0
            feat["properties"] = props
            continue

        # 매핑 조회
        info = dong_map.get(code) or dong_map.get(_normalize_code(code))
        if not info:
            props["risk_exists"] = False
            props["업종별_위험도"] = []
            props["업종_개수"] = 0
            feat["properties"] = props
            continue

        # 병합(대표 개념 없이 업종 배열만)
        matched += 1
        props["risk_exists"] = True
        props["행정동_코드"] = info["행정동_코드"]
        if info["행정동_코드_명"] is not None:
            props["행정동_명"] = info["행정동_코드_명"]
        props["업종별_위험도"] = info["업종별_위험도"]
        props["업종_개수"] = info["업종_개수"]

        feat["properties"] = props

    gj["features"] = feats

    # 저장
    with open(out_geojson_path, "w", encoding="utf-8") as f:
        json.dump(gj, f, ensure_ascii=False)

    print(f"[GeoJSON 병합] features={len(feats)}, 매칭 성공={matched}, 실패={len(feats)-matched}")
    print(f"저장 완료: {out_geojson_path}")

# 실행
_coerce_numeric_cols(out, ["risk100_all", "risk100_by_biz"], ndigits=1)
save_result_as_geojson(GEOJSON_SRC, GEOJSON_OUT, out)
