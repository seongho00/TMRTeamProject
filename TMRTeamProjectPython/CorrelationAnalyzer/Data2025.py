import os
import glob
import pandas as pd

# 원본 CSV에서 2025 폴더로 정리
source_dir = "C:/Users/user/Downloads/서울 데이터 2025"
target_dir = "C:/Users/user/Downloads/Seoul_data_2025"
os.makedirs(target_dir, exist_ok=True)

for file_path in glob.glob(os.path.join(source_dir, "*.csv")):
    try:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')

        if '행정동_코드_명' in df.columns:
            df['행정동_코드_명'] = df['행정동_코드_명'].apply(
                lambda x: x.replace('?', '·') if isinstance(x, str) and '?' in x else x
            )

            filename = os.path.basename(file_path)
            save_path = os.path.join(target_dir, filename)
            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"[저장 완료] {filename}")
        else:
            print(f"[컬럼 없음] {os.path.basename(file_path)}")

    except Exception as e:
        print(f"[에러] {os.path.basename(file_path)} | {e}")
