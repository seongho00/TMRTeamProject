import pandas as pd
import glob
import os

ANALYZER_PATH = "result_analyzer.csv"
CLUSTER_DIR = 'C:/Users/user/Downloads/업종별_병합결과_클로스터링'
SAVE_DIR = 'C:/Users/user/Downloads/업종별_최종결합'
os.makedirs(SAVE_DIR, exist_ok=True)

# 상관계수 위험도 결과 불러오기
risk_df = pd.read_csv(ANALYZER_PATH, encoding='utf-8-sig')
risk_df['행정동_코드'] = risk_df['행정동_코드'].astype(str)

# 모든 업종 클러스터링 결과 처리
for path in glob.glob(os.path.join(CLUSTER_DIR, '*_클러스터링.csv')):
    filename = os.path.basename(path)
    업종명 = filename.replace('_클러스터링.csv', '')

    try:
        df = pd.read_csv(path, encoding='utf-8-sig')
    except Exception as e:
        print(f"오류: {e}")
        continue

    if '행정동_코드' not in df.columns:
        print(f"{filename} → 행정동_코드 없음, 건너뜀")
        continue

    df['행정동_코드'] = df['행정동_코드'].astype(str)

    # 병합
    merged = pd.merge(df, risk_df, on='행정동_코드', how='left')

    # 저장
    save_path = os.path.join(SAVE_DIR, f"{업종명}_최종결합.csv")
    merged.to_csv(save_path, index=False, encoding='utf-8-sig')
    print(f"저장 완료: {save_path}")
