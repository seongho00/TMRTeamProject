import pandas as pd
import os
import glob

# 1. CSV 파일이 들어 있는 폴더 경로 지정
DATA_DIR = 'C:/Users/admin/Desktop/서울 데이터 모음집'  # 여기에 CSV 파일들이 들어 있는 폴더 경로 입력

# 2. '서울시 상권분석서비스'로 시작하는 모든 CSV 파일 탐색
csv_files = glob.glob(os.path.join(DATA_DIR, '서울시 상권분석서비스(*.csv'))

# 3. 각 파일을 읽어서 딕셔너리에 저장 (메모리 내에서만)
data_dict = {}

for file_path in csv_files:
    file_name = os.path.basename(file_path)
    name_without_ext = os.path.splitext(file_name)[0]

    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='cp949')  # 윈도우 한글 csv일 경우

    data_dict[name_without_ext] = df
    print(f"✅ 불러옴: {name_without_ext} → {df.shape[0]}행 {df.shape[1]}열")


data_dict['서울시 상권분석서비스(길단위인구-행정동)'].head()
data_dict['서울시 상권분석서비스(점포_매출-행정동)_2023년']