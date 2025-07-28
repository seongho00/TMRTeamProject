import pandas as pd
import os
import glob
import re
from collections import defaultdict

# 실제 경로로 수정
DATA_DIR = 'C:/Users/admin/Desktop/서울 데이터 모음집'

# 불러올 기간 범위
MIN_PERIOD = 20224
MAX_PERIOD = 20243

# 저장할 폴더 경로 지정 (없으면 생성)
SAVE_DIR = 'C:/Users/admin/Desktop/서울 데이터 가공'
os.makedirs(SAVE_DIR, exist_ok=True)

# 대상 파일 수집
csv_files = glob.glob(os.path.join(DATA_DIR, '서울시 상권분석서비스(*.csv'))
data_dict = {}

# 병합용 딕셔너리: {업종명: [df1, df2, ...]}
merged_dict = defaultdict(list)

for file_path in csv_files:
    filename = os.path.basename(file_path)

    # 파일명 → base_key 추출
    match = re.search(r'서울시 상권분석서비스\((.*?)\)', filename)
    base_name = match.group(1) if match else 'Unknown'
    year_match = re.search(r'(\d{4}년)', filename)
    year = year_match.group(1) if year_match else ''
    full_key = f"{base_name}_{year}" if year else base_name

    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='cp949')

    # 기간 필터
    if '기준_년분기_코드' in df.columns:
        df['기준_년분기_코드'] = df['기준_년분기_코드'].astype(int)
        df = df[(df['기준_년분기_코드'] >= MIN_PERIOD) & (df['기준_년분기_코드'] <= MAX_PERIOD)]

        # 필터 후 행이 없으면 제외
        if df.empty:
            print(f"⏩ 제외: {full_key} → 해당 기간 없음")
            continue

    # data_dict에 추가
    data_dict[full_key] = df
    print(f"✅ 포함: {full_key} → {df.shape[0]}행")

# 3. 병합용 dict 생성: 연도 제거한 base_key 기준
merged_dict = defaultdict(list)
for full_key, df in data_dict.items():
    base_key = re.sub(r'_\d{4}년$', '', full_key)
    merged_dict[base_key].append(df)

# 4. 병합 및 저장
for base_key, df_list in merged_dict.items():
    merged_df = pd.concat(df_list, ignore_index=True)
    filename = base_key.replace(' ', '_') + '.csv'
    save_path = os.path.join(SAVE_DIR, filename)
    merged_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"📁 저장 완료: {filename} → {merged_df.shape[0]}행")


# 1. 점포 데이터 (2022)
df_2022 = pd.read_csv('C:/Users/admin/Desktop/서울 데이터 모음집/서울시 상권분석서비스(점포-행정동)_2022년.csv', encoding='utf-8')
print("✅ 점포 2022년 포함 분기:", sorted(df_2022['기준_년분기_코드'].unique()))

# 2. 추정매출 데이터 (2023)
df_2023 = pd.read_csv('C:/Users/admin/Desktop/서울 데이터 모음집/서울시 상권분석서비스(추정매출-행정동)_2023년.csv', encoding='utf-8')
print("✅ 추정매출 2023년 포함 분기:", sorted(df_2023['기준_년분기_코드'].unique()))