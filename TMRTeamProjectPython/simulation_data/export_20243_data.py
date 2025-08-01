import pandas as pd
import os

# 1. 전처리 대상 폴더 경로 지정
input_folder = 'C:/Users/admin/Desktop/서울 데이터 모음집 - 복사본'  # 여기에 CSV들이 있는 폴더 경로를 입력하세요
output_folder = './filtered'  # 결과 저장 폴더

# 2. 결과 폴더가 없으면 생성
os.makedirs(output_folder, exist_ok=True)

# 3. 대상 분기
target_quarter = 20243



# 4. 전체 파일 처리
for filename in os.listdir(input_folder):
    if filename.endswith('.csv'):
        file_path = os.path.join(input_folder, filename)

        try:
            df = pd.read_csv(file_path, encoding='cp949')  # 필요시 cp949로 변경

            if '기준_년분기_코드' in df.columns:
                filtered_df = df[df['기준_년분기_코드'] == target_quarter]
                if not filtered_df.empty:
                    output_path = os.path.join(output_folder, f'filtered_2024Q3_{filename}')
                    filtered_df.to_csv(output_path, index=False, encoding='utf-8-sig')
                    print(f"{filename} → ✅ 필터링 완료 ({len(filtered_df)} rows)")
                else:
                    print(f"{filename} → ⚠️ 해당 분기 데이터 없음")
            else:
                print(f"{filename} → ❌ '기준_년분기_코드' 컬럼 없음")

        except Exception as e:
            print(f"{filename} → ❌ 오류 발생: {e}")
