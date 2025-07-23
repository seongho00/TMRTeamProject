import pandas as pd
import os

# 처리할 폴더 경로
input_folder = "./daejeon_population_original"
output_folder = "./daejeon_population_result"

# 월별 이름 매핑
month_map = {
    "202401": "1월", "202402": "2월", "202403": "3월", "202404": "4월",
    "202405": "5월", "202406": "6월", "202407": "7월", "202408": "8월",
    "202409": "9월", "202410": "10월", "202411": "11월", "202412": "12월"
}

# 출력 폴더 없으면 생성
os.makedirs(output_folder, exist_ok=True)

# 폴더 내 모든 파일 반복
for filename in os.listdir(input_folder):
    if filename.endswith(".csv"):
        filepath = os.path.join(input_folder, filename)

        # 파일 불러오기
        try:
            df = pd.read_csv(filepath, encoding="utf-8-sig")
        except UnicodeDecodeError:
            df = pd.read_csv(filepath, encoding="euc-kr")

        # '대전광역시' 데이터만 필터링
        daejeon_df = df[df["시도명"] == "대전광역시"].copy()

        # 월 정보 추출
        for mm in month_map:
            if mm in filename:
                month_name = month_map[mm]
                break
        else:
            month_name = "미정"

        # 연령대 범위 정의: (시작, 끝)
        age_ranges = [
            (0, 9),
            (10, 19),
            (20, 29),
            (30, 39),
            (40, 49),
            (50, 59),
            (60, 200)
        ]

        # 연령대별 컬럼 자동 생성
        for start, end in age_ranges:
            male_cols = [f"{age}세남자" for age in range(start, end + 1) if f"{age}세남자" in daejeon_df.columns]
            female_cols = [f"{age}세여자" for age in range(start, end + 1) if f"{age}세여자" in daejeon_df.columns]

            # 새 컬럼 이름 (예: age_10_19_male)
            male_col = f"age_{start}_{end}_male"
            female_col = f"age_{start}_{end}_female"
            total_col = f"age_{start}_{end}_total"

            daejeon_df.loc[:, male_col] = daejeon_df[male_cols].sum(axis=1)
            daejeon_df.loc[:, female_col] = daejeon_df[female_cols].sum(axis=1)
            daejeon_df.loc[:, total_col] = daejeon_df[male_col] + daejeon_df[female_col]

        # ✅ 나이별 개별 컬럼 삭제 (이 코드 추가!)
        cols_to_drop = [col for col in daejeon_df.columns if '세남자' in col or '세여자' in col]
        daejeon_df.drop(columns=cols_to_drop, inplace=True)

        # 결과 저장
        output_name = f"대전광역시_인구_{month_name}.csv"
        output_path = os.path.join(output_folder, output_name)
        daejeon_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ 저장 완료: {output_name}")
