import pandas as pd
import os
import glob

# 경로 설정
INPUT_DIR = 'C:/Users/admin/Desktop/업종별_병합결과 - 복사본'
OUTPUT_DIR = 'C:/Users/admin/Desktop/업종별_전처리결과'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 전처리 대상 컬럼 키워드
TARGET_KEYWORDS = ['매출', '상주인구', '직장', '소득', '지출', '점포', '아파트', '집객', '변화']

# 전처리 함수
def preprocess_dataframe(df):
    # 숫자형 변환 (콤마 제거, object → float)
    for col in df.columns:
        if any(keyword in col for keyword in TARGET_KEYWORDS):
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='coerce')

    # 결측치 처리 (필요 시 평균/중앙값으로 대체 가능)
    df = df.dropna(subset=['서비스_업종_코드', '행정동_코드'])  # 필수 키 누락 제거
    df = df.fillna(0)  # 나머지는 0으로 처리

    return df

# 전체 파일 반복
csv_files = glob.glob(os.path.join(INPUT_DIR, '*.csv'))

for file_path in csv_files:
    file_name = os.path.basename(file_path)
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
        df = preprocess_dataframe(df)
        df.to_csv(os.path.join(OUTPUT_DIR, file_name), index=False, encoding='utf-8-sig')
        print(f"✅ 전처리 완료: {file_name} → {df.shape[0]}행 {df.shape[1]}열")
    except Exception as e:
        print(f"❌ 오류 발생: {file_name} → {e}")
