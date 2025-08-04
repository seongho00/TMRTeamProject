import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

# CSV 병합 (1~4분기)
csv_paths = [
    "C:/Users/user/Downloads/서울_유동인구_매출_20241.csv",
    "C:/Users/user/Downloads/서울_유동인구_매출_20242.csv",
    "C:/Users/user/Downloads/서울_유동인구_매출_20243.csv",
    "C:/Users/user/Downloads/서울_유동인구_매출_20244.csv"
]

dfs = []
for path in csv_paths:
    df = pd.read_csv(path)
    df['기준_년분기_코드'] = df['기준_년분기_코드']
    df['행정동_코드'] = df['행정동_코드'].astype(str)
    dfs.append(df)

full_df = pd.concat(dfs, ignore_index=True)

# 상관계수 기반 위험도 계산 (레이블 생성)
risk_labels = []
grouped = full_df.groupby(['행정동_코드', '행정동_코드_명'])

for (code, name), group in grouped:
    if len(group) >= 2 and group['총_유동인구_수'].std() != 0 and group['당월_매출_금액'].std() != 0:
        corr = group['총_유동인구_수'].corr(group['당월_매출_금액'])
        score = 1 - corr if pd.notnull(corr) else None
        if score is not None:
            risk_labels.append({
                '행정동_코드': code,
                '상관_위험도점수': score
            })

risk_df = pd.DataFrame(risk_labels)

# 최신 분기 기준 입력 데이터 사용
latest_quarter_df = full_df[full_df['기준_년분기_코드'] == full_df['기준_년분기_코드'].max()]

# 병합
train_df = latest_quarter_df.merge(risk_df, on='행정동_코드')

# 모델 입력 변수 선택
features = ['총_유동인구_수', '남성_유동인구_수', '여성_유동인구_수', '연령대_10_유동인구_수', '연령대_20_유동인구_수',
            '연령대_30_유동인구_수', '연령대_40_유동인구_수', '연령대_50_유동인구_수', '연령대_60_이상_유동인구_수',
            '당월_매출_금액', '남성_매출_금액', '여성_매출_금액']

X = train_df[features]
y = train_df['상관_위험도점수']

# 학습/테스트 분리
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 모델 학습
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 예측 및 평가
y_pred = model.predict(X_test)
print("MSE:", mean_squared_error(y_test, y_pred))
print("R2:", r2_score(y_test, y_pred))

# 전체 데이터 예측
train_df['예측_위험도'] = model.predict(X)

# 결과 저장
train_df[['행정동_코드', '상관_위험도점수', '예측_위험도']].to_csv("rf_predicted_risk.csv", index=False, encoding='utf-8-sig')
