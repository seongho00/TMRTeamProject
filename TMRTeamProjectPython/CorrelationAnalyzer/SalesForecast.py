import glob
import os
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

df_dir = "C:/Users/user/Downloads/seoul_data_merge"
csv_files = glob.glob(os.path.join(df_dir, "*.csv"))

quarters = ['20231', '20232', '20233', '20234', '20241', '20242', '20243', '20244', '20251']

target_col = '당월_매출_금액'

features = [
    '점포_수', '개업_점포_수', '폐업_점포_수', '프랜차이즈_점포_수', '유사_업종_점포_수',
    '총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수',
    '총_직장_인구_수', '총_상주인구_수',
    '월_평균_소득_금액', '지출_총금액', '음식_지출_총금액'
]

for quarter in quarters:
    matched_files = [f for f in csv_files if quarter in f]
    if not matched_files:
        continue

    df = pd.read_csv(matched_files[0], encoding='utf-8')
    df = df[[col for col in df.columns if '아파트' not in col]]

    required_cols = features + [target_col, '행정동_코드', '행정동_코드_명']
    if not all(col in df.columns for col in required_cols):
        continue

    df = df[required_cols].dropna()

    # 행정동 기준으로 평균 집계
    grouped = df.groupby(['행정동_코드', '행정동_코드_명'])[features + [target_col]].mean().reset_index()

    X = grouped[features]
    y = grouped[target_col]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    print(f"[{quarter}] RMSE:", np.sqrt(mean_squared_error(y_test, y_pred)))
    print(f"[{quarter}] R²:", r2_score(y_test, y_pred))

    result_df = pd.DataFrame({
        '실제값': y_test,
        '예측값': y_pred
    })
    result_df.to_csv(f"C:/Users/user/Downloads/매출_예측_결과_{quarter}.csv", index=False, encoding='utf-8-sig')

    importances = pd.Series(model.feature_importances_, index=features).sort_values(ascending=True)
    plt.figure(figsize=(10, 7))
    importances.plot(kind='barh')
    plt.title(f'[{quarter}] 매출 예측 변수 중요도')
    plt.tight_layout()
    plt.show()

    plt.figure(figsize=(10, 5))
    plt.plot(y_test.values[:50], label='실제값')
    plt.plot(y_pred[:50], label='예측값')
    plt.legend()
    plt.title(f"[{quarter}] 실제 매출 vs 예측 매출")
    plt.xlabel("행정동 샘플")
    plt.ylabel("당월 매출 금액")
    plt.tight_layout()
    plt.show()

    # 지도용 저장
    test_index = y_test.index
    df_test = grouped.loc[test_index, ['행정동_코드', '행정동_코드_명']].copy()
    df_test['예측_매출'] = y_pred
    df_test['실제_매출'] = y_test.values
    df_test.to_csv(f"/map_result_{quarter}.csv", index=False, encoding='utf-8-sig')
    print(f"[{quarter}] 지도용 예측 결과 저장 완료")
