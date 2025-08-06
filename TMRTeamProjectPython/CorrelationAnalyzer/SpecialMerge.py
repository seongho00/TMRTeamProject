import os
import glob
import pandas as pd

df_dir = "C:/Users/user/Downloads/서울 데이터 모음집"
save_dir = "C:/Users/user/Downloads/Seoul_data"
os.makedirs(save_dir, exist_ok=True)

# 해당 폴더 안의 모든 csv 파일 가져오기
csv_files = glob.glob(os.path.join(df_dir, "*.csv"))

for file_path in csv_files:
    try:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='cp949')

        if '행정동_코드_명' in df.columns:
            df['행정동_코드_명'] = df['행정동_코드_명'].apply(
                lambda x: x.replace('?', '·') if isinstance(x, str) and '?' in x else x
            )

            # 저장 파일 이름 변경
            filename = os.path.basename(file_path)
            save_path = os.path.join(save_dir, filename)

            df.to_csv(save_path, index=False, encoding='utf-8-sig')
            print(f"처리 완료: {os.path.basename(file_path)}")
        else:
            print(f"컬럼 없음: {os.path.basename(file_path)}")

    except Exception as e:
        print(f"오류 발생: {os.path.basename(file_path)} | {e}")
