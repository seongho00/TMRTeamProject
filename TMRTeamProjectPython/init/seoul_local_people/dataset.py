import os.path

import pandas as pd

# csv 파일 경로
file = [
    "C:/Users/user/Downloads/서울_생활인구_2024_1분기_원본.csv",
    "C:/Users/user/Downloads/서울_생활인구_2024_2분기_원본.csv",
    "C:/Users/user/Downloads/서울_생활인구_2024_3분기_원본.csv",
    "C:/Users/user/Downloads/서울_생활인구_2024_4분기_원본.csv"
]

# 원본 일일별로 만들기
for i in range(len(file)):
    df = pd.read_csv(file[i], encoding='utf-8-sig')

    # 기준일ID와 행정동코드로 묶고 합치기
    df_group = df.groupby(['기준일ID', '행정동코드'], as_index=False).sum()

    # 잘못 만들어진 컬럼 제거 ['기준_년분기_코드']
    df_group = df_group.drop(['기준_년분기_코드', '시간대구분'], axis=1)

    # 일일 생활인구 데이터
    print(df_group)

    save_file = f"C:/Users/user/Downloads/서울_생활인구_2024_{i + 1}분기_일일별.csv"

    if os.path.exists(save_file):
        os.remove(save_file)

    df_group.to_csv(save_file, index=False, encoding='utf-8-sig')
    print("저장완료")

file_def = [
]

if not all(os.path.exists(f) for f in file_def):
    print("종료")
    exit()

for i in range(len(file_def)):
    df = pd.read_csv(file_def[i], encoding='utf-8-sig')

    # 일일별을 분기별로 만들기
    df_group['기준일ID'] = df['기준일ID'].astype(str)
    print(df_group['기준일ID'])

    a = df_group['기준일ID'].str[4:6].astype(int)
    print(a)

    def get_quarter_code(month):
        if 1 <= month <= 3:
            return 20241
        elif 4 <= month <= 6:
            return 20242
        elif 7 <= month <= 9:
            return 20243
        else:
            return 20244

    df_group['기준_년분기_코드'] = a.apply(get_quarter_code)

    # 분기별 합산
    df_quarter = df_group.groupby(['기준_년분기_코드', '행정동코드'], as_index=False).sum()

    # 저장
    save_file = f"C:/Users/user/Downloads/서울_생활인구_2024_{i + 1}분기.csv"
    df_quarter.to_csv(save_file, encoding='utf-8-sig')
    print("저장완료")
