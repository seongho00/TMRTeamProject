import glob
import os
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 설정
DATA_DIR = r"C:/Users/admin/Downloads/seoul_data_merge"
OUT_DIR = r"C:/Users/admin/Downloads"
Path(OUT_DIR).mkdir(parents=True, exist_ok=True)

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
    '폐업_률':0.4,
    '경쟁강도':0.2,
    '프랜차이즈비중':0.15,
    '주중주말편차':0.15,
    '연령의존도':0.1
}

def load_data():
    csv_files = glob.glob(os.path.join(DATA_DIR, "*.csv"))

    df_train = pd.concat([
        pd.read_csv(f) for f in csv_files if any(q in f for q in TRAIN_QUARTERS)
    ], ignore_index=True)

    df_test = pd.concat([
        pd.read_csv(f) for f in csv_files if TEST_QUARTER in f
    ], ignore_index=True)

    df_train = df_train[[c for c in df_train.columns if '아파트' not in c]]
    df_test  = df_test[[c for c in df_train.columns if '아파트' not in c]]

    return df_train, df_test

def build_clusters(df_train, df_test):
    feats = [c for c in CLUSTER_FEATURES if c in df_train.columns]
    if not feats:
        df_train['cluster'] = 0
        df_test['cluster'] = 0
        return df_train, df_test

    scaler = StandardScaler()
    Xc_tr = scaler.fit_transform(df_train[feats].fillna(0))
    km = KMeans(n_clusters=5, random_state=42, n_init=10)
    df_train['cluster'] = km.fit_predict(Xc_tr)

    Xc_te = scaler.transform(df_test[feats].fillna(0))
    df_test['cluster'] = km.predict(Xc_te)

    return df_train, df_test

def top_corr_features(df, k=20):
    cand = [c for c in CORR_CANDIDATES if c in df.columns and not any(b in c for b in BLOCK_LIST)]
    valid = [c for c in cand + [COR_TARGET] if c in df.columns]

    if COR_TARGET not in valid:
        return cand[:k]

    cor = df[valid].corr(numeric_only=True)
    order = (
        cor[[COR_TARGET]]
        .dropna()
        .sort_values(by=COR_TARGET, ascending=False)
        .drop(index=[COR_TARGET], errors='ignore')
        .head(k)
        .index.tolist()
    )
    return order

def add_risk_components(df):
    df = df.copy()

    # 경쟁강도: 유사_업종_점포_수 원값 사용
    if '유사_업종_점포_수' in df.columns:
        df['경쟁강도'] = df['유사_업종_점포_수'].fillna(0)
    else:
        df['경쟁강도'] = 0

    # 프랜차이즈비중: 비율 유지 (필요 시 원값으로 바꿀 수 있음)
    if all(c in df.columns for c in ['프랜차이즈_점포_수','점포_수']):
        denom = df['점포_수'].replace(0, np.nan)
        df['프랜차이즈비중'] = (df['프랜차이즈_점포_수'] / denom).fillna(0)
    else:
        df['프랜차이즈비중'] = 0

    # 주중/주말 매출 편차 비율
    if all(c in df.columns for c in ['주중_매출_금액','주말_매출_금액','당월_매출_금액']):
        diff = (df['주중_매출_금액'] - df['주말_매출_금액']).abs()
        denom = df['당월_매출_금액'].replace(0, np.nan)
        df['주중주말편차'] = (diff / denom).fillna(0)
    else:
        df['주중주말편차'] = 0

    # 연령 의존도(20~40 매출 집중도)
    if all(c in df.columns for c in ['연령대_20_매출_금액','연령대_30_매출_금액','연령대_40_매출_금액','당월_매출_금액']):
        core = df['연령대_20_매출_금액'] + df['연령대_30_매출_금액'] + df['연령대_40_매출_금액']
        denom = df['당월_매출_금액'].replace(0, np.nan)
        df['연령의존도'] = (core / denom).fillna(0)
    else:
        df['연령의존도'] = 0

    if '폐업_률' not in df.columns:
        df['폐업_률'] = 0

    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)
    return df

def risk_score_and_label(df_train, df_test, weights=RISK_WEIGHTS):
    scaler = StandardScaler()
    cols = [c for c in weights.keys() if c in df_train.columns]

    Z_tr = pd.DataFrame(scaler.fit_transform(df_train[cols]), columns=cols, index=df_train.index)
    Z_te = pd.DataFrame(scaler.transform(df_test[cols]), columns=cols, index=df_test.index)

    w = np.array([weights[c] for c in cols])
    df_train['위험도_점수'] = Z_tr.values @ w
    df_test['위험도_점수']  = Z_te.values @ w

    qs = df_train['위험도_점수'].quantile([0, 1/3, 2/3, 1]).values
    bins = np.unique(qs)
    if len(bins) < 4:
        # 분포 쏠림 대비 기본 구간
        bins = np.quantile(df_train['위험도_점수'], [0, 1/3, 2/3, 1]).tolist()

    df_train['위험도'] = pd.cut(df_train['위험도_점수'], bins=bins, labels=[0,1,2], include_lowest=True, duplicates='drop').astype(int)
    df_test['위험도']  = pd.cut(df_test['위험도_점수'],  bins=bins, labels=[0,1,2], include_lowest=True, duplicates='drop')
    df_test = df_test[df_test['위험도'].notna()].copy()
    df_test['위험도'] = df_test['위험도'].astype(int)
    return df_train, df_test

def train_and_eval(df_train, df_test):
    top_feats = top_corr_features(df_train, k=20)
    feature_cols = list(dict.fromkeys(top_feats + ['cluster']))
    X_tr = df_train[feature_cols].fillna(0)
    y_tr = df_train['위험도']
    X_te = df_test[feature_cols].fillna(0)
    y_te = df_test['위험도']

    rf = RandomForestClassifier(n_estimators=1, warm_start=True, random_state=42, n_jobs=-1)
    total_trees = 300
    for i in tqdm(range(1, total_trees + 1), desc="학습 진행률", unit="트리"):
        rf.n_estimators = i
        rf.fit(X_tr, y_tr)

    y_pred = rf.predict(X_te)
    print(classification_report(y_te, y_pred))

    importances = pd.Series(rf.feature_importances_, index=feature_cols).sort_values(ascending=True)
    plt.figure(figsize=(10,7))
    importances.plot(kind='barh')
    plt.title('위험도 예측 - 변수 중요도 (23~24 학습 → 25-1 테스트)')
    plt.tight_layout()
    plt.show()

    code_cols = [c for c in ['행정동_코드','행정동_코드_명'] if c in df_test.columns]
    if code_cols:
        out = df_test[code_cols].copy()
        out['예측_위험도'] = y_pred
        out['실제_위험도'] = y_te.values
        out_path = os.path.join(OUT_DIR, "위험도_예측결과_20251.csv")
        out.to_csv(out_path, index=False, encoding='utf-8-sig')
        print("저장:", out_path)

# 실행
df_train, df_test = load_data()
df_train, df_test = build_clusters(df_train, df_test)

df_train = add_risk_components(df_train)
df_test  = add_risk_components(df_test)

df_train, df_test = risk_score_and_label(df_train, df_test, weights=RISK_WEIGHTS)
train_and_eval(df_train, df_test)
