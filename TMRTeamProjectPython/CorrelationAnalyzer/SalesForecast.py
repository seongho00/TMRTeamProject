import glob
import os
import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.inspection import permutation_importance

import matplotlib.pyplot as plt

# ===== 공통 설정 =====
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# ===== 경로/기본 변수 =====
df_dir = r"C:/Users/admin/Downloads/seoul_data_merge"
out_dir = r"C:/Users/admin/Downloads"
Path(out_dir).mkdir(parents=True, exist_ok=True)

quarters = ['20231','20232','20233','20234','20241','20242','20243','20244','20251']
target_col = '당월_매출_금액'

base_features = [
    '점포_수','개업_점포_수','폐업_점포_수','프랜차이즈_점포_수','유사_업종_점포_수',
    '총_유동인구_수','남성_유동인구_수','여성_유동인구_수',
    '총_직장_인구_수','총_상주인구_수',
    '월_평균_소득_금액','지출_총금액','음식_지출_총금액',
    '주중_매출_금액','주말_매출_금액','남성_매출_금액','여성_매출_금액'
]

id_cols = ['행정동_코드', '행정동_코드_명']

def read_csv_safely(path):
    try:
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='cp949')

def build_features(df):
    df = df.copy()
    # 불필요 컬럼 제거
    df = df[[c for c in df.columns if '아파트' not in c]]
    # 필요한 컬럼만 보존 (존재하는 것만)
    keep = [c for c in (id_cols + base_features + [target_col]) if c in df.columns]
    df = df[keep]

    # 파생 변수
    def safe_div(a, b):
        b = b.replace(0, np.nan)
        return (a / b).fillna(0)

    if '프랜차이즈_점포_수' in df.columns:
        df['프랜차이즈_점포수'] = df['프랜차이즈_점포_수']
    if '유사_업종_점포_수' in df.columns:
        df['유사업종_점포수'] = df['유사_업종_점포_수']
    if {'총_유동인구_수','총_상주인구_수'}.issubset(df.columns):
        df['유동인구_상주비'] = safe_div(df['총_유동인구_수'], df['총_상주인구_수'])
    if {'총_직장_인구_수','총_상주인구_수'}.issubset(df.columns):
        df['직장인_비율'] = safe_div(df['총_직장_인구_수'], df['총_상주인구_수'])
    if {'주중_매출_금액','주말_매출_금액'}.issubset(df.columns):
        df['주중주말_매출비'] = safe_div(df['주중_매출_금액'], df['주말_매출_금액'])
    if {'남성_매출_금액','여성_매출_금액'}.issubset(df.columns):
        df['성별_매출비'] = safe_div(df['남성_매출_금액'], df['여성_매출_금액'])

    df.replace([np.inf, -np.inf], 0, inplace=True)
    df.fillna(0, inplace=True)
    return df

def evaluate_and_save(quarter, grouped, features, target, out_base):
    # 학습/평가 분리
    X = grouped[features].values
    y = grouped[target].values
    X_train, X_test, y_train, y_test, idx_train, idx_test = train_test_split(
        X, y, grouped.index, test_size=0.2, random_state=42
    )

    # 모델
    model = RandomForestRegressor(
        n_estimators=500,
        random_state=42,
        n_jobs=-1,
        max_features=1.0,
        oob_score=False
    )
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    # 성능
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    print(f"[{quarter}] RMSE: {rmse:.3f}")
    print(f"[{quarter}] R²  : {r2:.4f}")

    # 결과 저장
    result_df = pd.DataFrame({
        '기준_년분기_코드': quarter,
        '행정동_코드': grouped.loc[idx_test, '행정동_코드'].values,
        '행정동_코드_명': grouped.loc[idx_test, '행정동_코드_명'].values,
        '실제값': y_test,
        '예측값': y_pred
    })
    result_path = os.path.join(out_base, f"매출_예측_결과_{quarter}.csv")
    result_df.to_csv(result_path, index=False, encoding='utf-8-sig')

    # 중요도 저장/시각화
    importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=True)
    imp_path = os.path.join(out_base, f"변수중요도_{quarter}.csv")
    importances.sort_values(ascending=False).to_csv(imp_path, header=['importance'], encoding='utf-8-sig')

    plt.figure(figsize=(10, 7))
    importances.plot(kind='barh')
    plt.title(f'[{quarter}] 매출 예측 변수 중요도')
    plt.tight_layout()
    plt.show()

    # 예측 vs 실제 (일부)
    plt.figure(figsize=(10, 5))
    n_show = min(50, len(y_test))
    plt.plot(np.arange(n_show), y_test[:n_show], label='실제값')
    plt.plot(np.arange(n_show), y_pred[:n_show], label='예측값')
    plt.legend()
    plt.title(f"[{quarter}] 실제 매출 vs 예측 매출")
    plt.xlabel("샘플 인덱스")
    plt.ylabel(target_col)
    plt.tight_layout()
    plt.show()

    # permutation importance (옵션)
    try:
        perm = permutation_importance(model, X_test, y_test, n_repeats=10, random_state=42, scoring='neg_mean_squared_error')
        perm_df = pd.DataFrame({
            'feature': features,
            'importance_mean': perm.importances_mean,
            'importance_std': perm.importances_std
        }).sort_values('importance_mean', ascending=True)

        plt.figure(figsize=(10, 7))
        plt.barh(perm_df['feature'], perm_df['importance_mean'], xerr=perm_df['importance_std'])
        plt.title(f'[{quarter}] Permutation Importance (neg MSE)')
        plt.tight_layout()
        plt.show()
    except Exception:
        pass

    # 지도용 저장 (테스트 세트 기준)
    map_df = grouped.loc[idx_test, ['행정동_코드','행정동_코드_명']].copy()
    map_df['예측_매출'] = y_pred
    map_df['실제_매출'] = y_test
    map_path = os.path.join(out_base, f"map_result_{quarter}.csv")
    map_df.to_csv(map_path, index=False, encoding='utf-8-sig')
    print(f"[{quarter}] 결과 저장 완료: {result_path}, {imp_path}, {map_path}")

# ===== 메인 루프 =====
csv_files = glob.glob(os.path.join(df_dir, "*.csv"))

for quarter in quarters:
    matched_files = [f for f in csv_files if quarter in f]
    if not matched_files:
        print(f"[{quarter}] 파일 없음, 건너뜀")
        continue

    # 분기 내 다수 파일이면 모두 병합
    df_list = [read_csv_safely(f) for f in matched_files]
    df_q = pd.concat(df_list, ignore_index=True)

    # 피처 구성
    df_q = build_features(df_q)

    # 필수 컬럼 확인
    required = set(id_cols + [target_col])
    if not required.issubset(df_q.columns):
        print(f"[{quarter}] 필수 컬럼 누락, 건너뜀 -> 누락: {sorted(required - set(df_q.columns))}")
        continue

    # 집계 (행정동 단위 평균)
    keep_features = [c for c in df_q.columns if c not in id_cols and c != target_col]
    grouped = (
        df_q[id_cols + keep_features + [target_col]]
        .groupby(id_cols, as_index=False)
        .mean(numeric_only=True)
    )

    # 모델 입력 피처 선정
    features = [c for c in keep_features if grouped[c].dtype != 'O']

    # 학습/평가/저장
    evaluate_and_save(quarter, grouped, features, target_col, out_dir)
