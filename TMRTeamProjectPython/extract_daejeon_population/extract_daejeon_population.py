import pandas as pd
import os

# 처리할 폴더 경로
input_folder = "C:/Users/admin/Desktop/2024년 대전 성별, 연령별 인구수"
output_folder = "./daejeon_population"

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
        daejeon_df = df[df["시도명"] == "대전광역시"]

        # 월 정보 추출
        for mm in month_map:
            if mm in filename:
                month_name = month_map[mm]
                break
        else:
            month_name = "미정"

        # 결과 저장
        output_name = f"대전광역시_인구_{month_name}.csv"
        output_path = os.path.join(output_folder, output_name)
        daejeon_df.to_csv(output_path, index=False, encoding="utf-8-sig")
        print(f"✅ 저장 완료: {output_name}")
