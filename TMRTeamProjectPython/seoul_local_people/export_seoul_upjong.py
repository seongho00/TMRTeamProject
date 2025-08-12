import pandas as pd

# 1. CSV 파일 경로 설정 (경로에 맞게 수정하세요)
input_path = "C:/Users/qjvpd/OneDrive/바탕 화면/서울시_상권분석서비스(추정매출-행정동)_2023년.csv"
output_path = "서비스_업종_코드_목록.csv"

# 2. CSV 불러오기
df = pd.read_csv(input_path, encoding="cp949")

# 3. '서비스_업종_코드' 컬럼에서 중복 제거
unique_codes = df[['서비스_업종_코드','서비스_업종_코드_명']].drop_duplicates()

# 4. 새 CSV로 저장
unique_codes.to_csv(output_path, index=False, encoding='utf-8-sig')

print(f"총 {len(unique_codes)}개의 고유 업종 코드가 저장되었습니다.")