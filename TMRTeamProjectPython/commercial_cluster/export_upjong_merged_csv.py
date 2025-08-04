import glob
import os

import pandas as pd

# 1. 데이터 폴더 설정
DATA_DIR = 'C:/Users/user/Downloads/서울 데이터 가공'
SAVE_DIR = 'C:/Users/user/Downloads/업종별_병합결과'
os.makedirs(SAVE_DIR, exist_ok=True)

# 2. CSV 불러오기
csv_files = glob.glob(os.path.join(DATA_DIR, '*.csv'))
data_dict = {}

for file_path in csv_files:
    file_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(file_name)[0]

    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='cp949')

    data_dict[name_without_ext] = df
    print(f"✅ 불러옴: {name_without_ext} → {df.shape[0]}행 {df.shape[1]}열")

# 3. 기준 키 설정
area_keys = ['기준_년분기_코드', '행정동_코드']
upjong_keys = area_keys + ['서비스_업종_코드']


# 4. 업종별 병합 시작
base_df = data_dict.get('점포-행정동')
if base_df is None or '서비스_업종_코드' not in base_df.columns:
    print("❗ '점포-행정동' 파일이 없거나 '서비스_업종_코드'가 없습니다.")
    exit()


for code in base_df['서비스_업종_코드'].dropna().unique():
    filtered_df = base_df[base_df['서비스_업종_코드'] == code].copy()

    # 업종 포함된 데이터 병합 (ex: 추정매출)
    if '추정매출-행정동' in data_dict:
        sales_df = data_dict['추정매출-행정동']
        filtered_sales = sales_df[sales_df['서비스_업종_코드'] == code]
        filtered_df = pd.merge(filtered_df, filtered_sales, on=upjong_keys, how='left')

    # 지역 기반 데이터 병합 (서비스_업종_코드 없음)
    for name in [
        '상주인구-행정동', '직장인구-행정동', '소득소비-행정동',
        '아파트-행정동', '상권변화지표-행정동', '집객시설-행정동', '길단위인구-행정동'
    ]:
        if name in data_dict:
            area_df = data_dict[name]
            # ✅ 중복 컬럼 제거 (병합 충돌 방지)
            drop_cols = [col for col in area_df.columns if col not in area_keys and col in filtered_df.columns]
            if drop_cols:
                print(f"⚠️ {name} 병합 전 중복 컬럼 제거: {drop_cols}")
                area_df.drop(columns=drop_cols, inplace=True)

            filtered_df = pd.merge(filtered_df, area_df, on=area_keys, how='left')

    # 파일명 구성
    if '서비스_업종_코드_명' in filtered_df.columns:
        name = filtered_df['서비스_업종_코드_명'].iloc[0].replace('/', '_').replace(' ', '_')
        filename = f"{code}_{name}.csv"
    else:
        filename = f"{code}.csv"

    # ✅ 병합 후 _x, _y 컬럼 정리
    if '서비스_업종_코드_명_x' in filtered_df.columns:
        filtered_df['서비스_업종_코드_명'] = filtered_df['서비스_업종_코드_명_x']
        filtered_df.drop(columns=['서비스_업종_코드_명_x', '서비스_업종_코드_명_y'], errors='ignore', inplace=True)

    if '행정동_코드_명_x' in filtered_df.columns:
        filtered_df['행정동_코드_명'] = filtered_df['행정동_코드_명_x']
        filtered_df.drop(columns=['행정동_코드_명_x', '행정동_코드_명_y'], errors='ignore', inplace=True)

    # ✅ 원하는 컬럼 순서로 정렬
    fixed_columns = [
        '기준_년분기_코드', '행정동_코드', '행정동_코드_명',
        '서비스_업종_코드', '서비스_업종_코드_명'
    ]
    # fixed_columns를 앞으로, 나머지는 뒤에 이어붙이기
    rest_columns = [col for col in filtered_df.columns if col not in fixed_columns]
    filtered_df = filtered_df[fixed_columns + rest_columns]

    # 🔽 파일명 구성
    if '서비스_업종_코드_명' in filtered_df.columns:
        upjong_name = str(filtered_df['서비스_업종_코드_명'].iloc[0])
        upjong_name = upjong_name.replace('/', '_').replace(' ', '_').replace('?', '').strip()
        filename = f"{code}_{upjong_name}.csv"
    else:
        filename = f"{code}.csv"

    # 저장
    save_path = os.path.join(SAVE_DIR, filename)
    filtered_df.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"📁 저장 완료: {filename} → {filtered_df.shape[0]}행")
