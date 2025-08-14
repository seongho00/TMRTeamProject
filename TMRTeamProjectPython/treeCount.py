# -*- coding: utf-8 -*-
# ============================================================
# 파일명 예시: rf_n_estimators_benchmark.py
# 목적: 랜덤포레스트 트리 개수(n_estimators)별 성능/시간 비교
# - 학습: 20221~20244 (사용 가능한 파일만 자동 로드)
# - 테스트: 20251
# - 군집 변수(selected_features), 상관분석 변수(correlation_features) 고정
# - 위험도 라벨: 5분위(0~4)
# - 출력: 결과 CSV 및 콘솔 표
# 준비:
#   pip install pandas scikit-learn tqdm
# 경로/파일명은 아래 CONFIG에서 수정
# ============================================================

import os
import time
import warnings
import numpy as np
import pandas as pd
from collections import Counter

from tqdm import tqdm
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
from sklearn.utils.class_weight import compute_class_weight

warnings.filterwarnings("ignore", message="class_weight presets .* are not recommended for warm_start")

# -----------------------------
# CONFIG
# -----------------------------
DATA_DIR = r"C:/Users/admin/Downloads/seoul_data_merge"
OUT_DIR = r"C:/Users/admin/Downloads/Seoul_RandomForest"
os.makedirs(OUT_DIR, exist_ok=True)

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
    "서울_데이터_병합_20244.csv",
]
TEST_FILE = "서울_데이터_병합_20251.csv"

# 비교할 트리 개수 목록
N_LIST = [50, 100, 200, 300, 400, 600, 800]

# 식별/그룹 기준 컬럼
ID_COLS = ['행정동_코드', '행정동_코드_명', '서비스_업종_코드', '서비스_업종_코드_명']

# 군집 변수(selected_features)
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

# 상관분석 변수(correlation_features)
correlation_features = []
correlation_features += [
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '연령대_10_유동인구_수', '연령대_20_유동인구_수', '연령대_30_유동인구_수',
    '연령대_40_유동인구_수', '연령대_50_유동인구_수', '연령대_60_이상_유동인구_수',
    '시간대_유동인구_수_00~06', '시간대_유동인구_수_06~11', '시간대_유동인구_수_11~14',
    '시간대_유동인구_수_14~17', '시간대_유동인구_수_17~21', '시간대_유동인구_수_21~24',
    '요일별_유동인구_수_평일', '요일별_유동인구_수_주말'
]
correlation_features += [
    '당월_매출_금액', '주중_매출_금액', '주말_매출_금액',
    '요일_매출_월요일', '요일_매출_화요일', '요일_매출_수요일', '요일_매출_목요일',
    '요일_매출_금요일', '요일_매출_토요일', '요일_매출_일요일',
    '남성_매출_금액', '여성_매출_금액',
    '연령대_10_매출_금액', '연령대_20_매출_금액', '연령대_30_매출_금액',
    '연령대_40_매출_금액', '연령대_50_매출_금액', '연령대_60_이상_매출_금액'
]
correlation_features += [
    '총_상주인구_수', '남성_상주인구_수', '여성_상주인구_수',
    '연령대_10_상주인구_수', '연령대_20_상주인구_수', '연령대_30_상주인구_수',
    '연령대_40_상주인구_수', '연령대_50_상주인구_수', '연령대_60_이상_상주인구_수',
    '총_가구_수'
]
correlation_features += [
    '월_평균_소득_금액', '지출_총금액',
    '식료품_지출_금액', '의류_신발_지출_금액', '생활용품_지출_금액',
    '의료비_지출_금액', '여가_지출_금액', '문화_지출_금액'
]
correlation_features += [
    '점포_수', '프랜차이즈_점포_수', '개업_점포_수', '폐업_점포_수', '유사_업종_점포_수'
]
correlation_features += [
    '총_직장_인구_수', '남성_직장_인구_수', '여성_직장_인구_수',
    '연령대_10_직장_인구_수', '연령대_20_직장_인구_수', '연령대_30_직장_인구_수',
    '연령대_40_직장_인구_수', '연령대_50_직장_인구_수', '연령대_60_이상_직장_인구_수'
]

# 위험도 가중치
RISK_WEIGHTS = {
    '경쟁강도': 0.20,        # 유사_업종_점포_수
    '프랜차이즈비중': 0.15,  # 프랜차이즈_점포_수 / 점포_수
    '주중주말편차': 0.25,    # |주중 - 주말| / 당월
    '연령의존도': 0.10,      # (20+30+40 매출) / 당월
    '폐업_률': 0.30          # 폐업_률 자체
}

# ------------------------------------------------------------
# 유틸/전처리 함수들
# ------------------------------------------------------------
def read_csv_any(path):
    """CSV를 UTF-8 → CP949 순으로 시도해 읽기"""
    try:
        return pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding="cp949")

def unify_columns(df: pd.DataFrame) -> pd.DataFrame:
    """컬럼명 공백 제거 + 중복 제거"""
    df = df.rename(columns=lambda c: str(c).strip())
    df = df.loc[:, ~df.columns.duplicated()].copy()
    return df

def ensure_numeric(df: pd.DataFrame, cols):
    """지정 컬럼을 숫자로 강제 변환"""
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    return df

def add_cluster_features(df_train, df_test, feats, n_clusters=5, random_state=42):
    """선택 피처로 KMeans 클러스터 추가"""
    feats = [c for c in feats if c in df_train.columns and c in df_test.columns]
    if not feats:
        df_train['cluster'] = 0
        df_test['cluster'] = 0
        return df_train, df_test

    for d in (df_train, df_test):
        d[feats] = d[feats].replace([np.inf, -np.inf], np.nan).fillna(0)

    scaler = StandardScaler()
    Xtr = scaler.fit_transform(df_train[feats].values)
    Xte = scaler.transform(df_test[feats].values)

    if Xtr.shape[0] < n_clusters:
        df_train['cluster'] = 0
        df_test['cluster'] = 0
        return df_train, df_test

    km = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df_train['cluster'] = km.fit_predict(Xtr)
    df_test['cluster'] = km.predict(Xte)
    return df_train, df_test

def add_risk_components(df):
    """경쟁강도/프랜차이즈비중/주중주말편차/연령의존도 파생 + 결측/무한 처리"""
    df = df.copy()

    if '유사_업종_점포_수' in df.columns:
        df['경쟁강도'] = df['유사_업종_점포_수'].fillna(0)
    else:
        df['경쟁강도'] = 0

    if all(c in df.columns for c in ['프랜차이즈_점포_수', '점포_수']):
        denom = df['점포_수'].replace(0, np.nan)
        df['프랜차이즈비중'] = (df['프랜차이즈_점포_수'] / denom).fillna(0)
    else:
        df['프랜차이즈비중'] = 0

    if all(c in df.columns for c in ['주중_매출_금액', '주말_매출_금액', '당월_매출_금액']):
        diff = (df['주중_매출_금액'] - df['주말_매출_금액']).abs()
        denom = df['당월_매출_금액'].replace(0, np.nan)
        df['주중주말편차'] = (diff / denom).fillna(0)
    else:
        df['주중주말편차'] = 0

    if all(c in df.columns for c in ['연령대_20_매출_금액','연령대_30_매출_금액','연령대_40_매출_금액','당월_매출_금액']):
        core = df['연령대_20_매출_금액'] + df['연령대_30_매출_금액'] + df['연령대_40_매출_금액']
        denom = df['당월_매출_금액'].replace(0, np.nan)
        df['연령의존도'] = (core / denom).fillna(0)
    else:
        df['연령의존도'] = 0

    if '폐업_률' not in df.columns:
        df['폐업_률'] = 0

    df = df.replace([np.inf, -np.inf], 0).fillna(0)
    return df

def risk_score_label(train_df, test_df, weights=RISK_WEIGHTS):
    """가중합 위험도 점수 → 5분위 라벨(0~4) 생성"""
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

    qs = train_df['위험도_점수'].quantile([i/5 for i in range(6)]).values
    bins = np.unique(qs).tolist()
    if len(bins) < 6:
        mn, mx = float(train_df['위험도_점수'].min()), float(train_df['위험도_점수'].max())
        if mn == mx:
            mn, mx = mn - 1e-6, mx + 1e-6
        bins = [mn + (mx - mn) * i / 5 for i in range(6)]

    num_labels = [0, 1, 2, 3, 4]
    train_df['위험도'] = pd.cut(train_df['위험도_점수'], bins=bins, labels=num_labels, include_lowest=True).astype(int)
    test_df['위험도']  = pd.cut(test_df['위험도_점수'],  bins=bins, labels=num_labels, include_lowest=True)
    test_df = test_df[test_df['위험도'].notna()].copy()
    test_df['위험도'] = test_df['위험도'].astype(int)

    return train_df, test_df

def corr_analysis(df: pd.DataFrame, target='당월_매출_금액', features=None, top_k=30):
    """피어슨 상관계수 기준 상위 top_k 피처 반환"""
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
    return ranking.index.tolist()

# ------------------------------------------------------------
# 메인 로직
# ------------------------------------------------------------
def main():
    # 1) 데이터 로드
    train_frames = []
    for fn in TRAIN_FILES:
        path = os.path.join(DATA_DIR, fn)
        if os.path.exists(path):
            train_frames.append(read_csv_any(path))
    if not train_frames:
        raise FileNotFoundError("학습용 CSV(20221~20244) 파일이 없습니다.")
    df_train_raw = pd.concat(train_frames, ignore_index=True)

    test_path = os.path.join(DATA_DIR, TEST_FILE)
    if not os.path.exists(test_path):
        raise FileNotFoundError("테스트 CSV(20251) 파일이 없습니다.")
    df_test_raw = read_csv_any(test_path)

    # 2) 컬럼 정리
    df_train_raw = unify_columns(df_train_raw)
    df_test_raw  = unify_columns(df_test_raw)

    # 3) 식별 컬럼 체크
    keep_ids = [c for c in ID_COLS if c in df_test_raw.columns]
    if not keep_ids:
        raise ValueError("테스트 데이터에 식별 컬럼(행정동/업종)이 없습니다.")

    # 4) 군집 피처
    df_train_clu, df_test_clu = add_cluster_features(
        df_train_raw.copy(), df_test_raw.copy(),
        selected_features, n_clusters=5, random_state=42
    )

    # 5) 위험 파생 + 5분위 라벨
    df_train_feat = add_risk_components(df_train_clu)
    df_test_feat  = add_risk_components(df_test_clu)
    df_train_feat, df_test_feat = risk_score_label(df_train_feat, df_test_feat, weights=RISK_WEIGHTS)

    # 6) 상관분석으로 상위 피처 선택
    top_corr = corr_analysis(df_train_feat, target='당월_매출_금액', features=correlation_features, top_k=30)

    # 7) 학습/예측 입력 피처 구성
    base_features = list(top_corr) + ['cluster', '경쟁강도', '프랜차이즈비중', '주중주말편차', '연령의존도', '폐업_률']
    base_features = [c for c in base_features if c in df_train_feat.columns and c in df_test_feat.columns]

    X_tr = df_train_feat[base_features].replace([np.inf, -np.inf], 0).fillna(0).values
    y_tr = df_train_feat['위험도'].astype(int).values
    X_te = df_test_feat[base_features].replace([np.inf, -np.inf], 0).fillna(0).values
    y_te = df_test_feat['위험도'].astype(int).values

    print("학습/평가 데이터 크기:", X_tr.shape, X_te.shape)
    print("레이블 분포(train/test):", Counter(y_tr), Counter(y_te))

    # 8) class_weight 직접 계산(경고 방지/불균형 보정)
    classes = np.unique(y_tr)
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_tr)
    class_weights = dict(zip(classes, weights))

    # 9) n_estimators 벤치마크
    records = []
    print("\n=== n_estimators 벤치마크 시작 ===")
    for n in N_LIST:
        # 진행 상황 출력
        print(f"\n>> 트리 개수: {n}")

        # 모델 생성
        rf = RandomForestClassifier(
            n_estimators=n,
            random_state=42,
            n_jobs=-1,
            class_weight=class_weights
        )

        # 학습 시간 측정
        t0 = time.perf_counter()
        rf.fit(X_tr, y_tr)
        train_sec = time.perf_counter() - t0

        # 예측/평가 시간 측정
        t1 = time.perf_counter()
        pred = rf.predict(X_te)
        infer_sec = time.perf_counter() - t1

        # 성능 지표 계산
        acc = accuracy_score(y_te, pred)
        f1_macro = f1_score(y_te, pred, average='macro', zero_division=0)
        f1_weighted = f1_score(y_te, pred, average='weighted', zero_division=0)

        print(f"정확도: {acc:.4f} | F1-macro: {f1_macro:.4f} | F1-weighted: {f1_weighted:.4f}")
        print(f"학습시간: {train_sec:.2f}s | 예측시간: {infer_sec:.2f}s")

        records.append({
            "n_estimators": n,
            "accuracy": acc,
            "f1_macro": f1_macro,
            "f1_weighted": f1_weighted,
            "train_sec": train_sec,
            "infer_sec": infer_sec
        })

    # 10) 결과 저장
    res = pd.DataFrame(records)
    res = res.sort_values(by=["f1_macro", "accuracy"], ascending=[False, False]).reset_index(drop=True)
    out_csv = os.path.join(OUT_DIR, "rf_n_estimators_benchmark.csv")
    res.to_csv(out_csv, index=False, encoding="utf-8-sig")

    print("\n=== 정렬된 결과 (상위 10) ===")
    print(res.head(10))
    print(f"\n저장 완료: {out_csv}")

    # 11) 최적 선택 안내(참고)
    best_row = res.iloc[0]
    print(f"\n권장 n_estimators: {int(best_row['n_estimators'])}  "
          f"(F1-macro={best_row['f1_macro']:.4f}, Acc={best_row['accuracy']:.4f}, "
          f"Train={best_row['train_sec']:.2f}s)")

if __name__ == "__main__":
    main()
