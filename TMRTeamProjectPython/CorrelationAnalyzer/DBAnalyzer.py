import pandas as pd

# 유동인구 + 매출 데이터 경로 설정 (1~4분기)
df_paths = {
    "20241": "C:/Users/user/Downloads/서울_유동인구_매출_20241.csv",
    "20242": "C:/Users/user/Downloads/서울_유동인구_매출_20242.csv",
    "20243": "C:/Users/user/Downloads/서울_유동인구_매출_20243.csv",
    "20244": "C:/Users/user/Downloads/서울_유동인구_매출_20244.csv"
}

# 점포 데이터 불러오기 및 전처리
shop_df = pd.read_csv("C:/Users/user/Downloads/서울시 상권분석서비스(점포-행정동)_2024년.csv", encoding='cp949')
shop_df['행정동_코드'] = shop_df['행정동_코드'].astype(str)
shop_df['기준_년분기_코드'] = shop_df['기준_년분기_코드'].astype(str)
shop_df['서비스_업종_코드'] = shop_df['서비스_업종_코드'].astype(str)

# 소득소비 데이터 불러오기 및 전처리
income_df = pd.read_csv("C:/Users/user/Downloads/서울시 상권분석서비스(소득소비-행정동).csv", encoding='cp949')
income_df['행정동_코드'] = income_df['행정동_코드'].astype(str)
income_df['기준_년분기_코드'] = income_df['기준_년분기_코드'].astype(str)

# 분기별 병합 및 저장
for quarter_code, path in df_paths.items():
    print(f"처리 중: {quarter_code}")

    # 유동인구+매출 데이터 불러오기 및 전처리
    df = pd.read_csv(path)
    df['행정동_코드'] = df['행정동_코드'].astype(str)
    df['기준_년분기_코드'] = df['기준_년분기_코드'].astype(str)
    df['서비스_업종_코드'] = df['서비스_업종_코드'].astype(str)

    # 점포 데이터 병합
    shop_q = shop_df[shop_df['기준_년분기_코드'] == quarter_code]
    merged = pd.merge(df, shop_q, on=['행정동_코드', '기준_년분기_코드', '서비스_업종_코드'], how='left')

    # 소득소비 데이터 병합
    income_q = income_df[income_df['기준_년분기_코드'] == quarter_code]
    merged = pd.merge(merged, income_q, on=['행정동_코드', '기준_년분기_코드'], how='left')

    # 결과 저장
    save_path = f"C:/Users/user/Downloads/서울시_상권분석_데이터_행정동_{quarter_code}.csv"
    merged.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {save_path}")
