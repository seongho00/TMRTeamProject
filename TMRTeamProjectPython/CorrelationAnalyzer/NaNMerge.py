import os

import pandas as pd

save_dir = "C:/Users/user/Downloads/seoul_data_merge"
os.makedirs(save_dir, exist_ok=True)
df_dir = "C:/Users/user/Downloads/Seoul_Merge_Data"
sp_dir = "C:/Users/user/Downloads/Seoul_Data_Special"

# 연도별 분기 리스트 정의
quarters_by_year = {
    2023: [20231, 20232, 20233, 20234],
    2024: [20241, 20242, 20243, 20244],
    2025: [20251]
}

for year, quarters in quarters_by_year.items():
    for quarter in quarters:
        df_path = os.path.join(df_dir, f"서울_상권분석_행정동_{quarter}.csv")
        sp_path = os.path.join(sp_dir, f"서울_상권분석_서비스업종포함_행정동_{quarter}.csv")

        if not (os.path.exists(df_path) and os.path.exists(sp_path)):
            print(f"[스킵] {quarter} → 파일이 존재하지 않음")
            continue

        df = pd.read_csv(df_path, encoding='utf-8')
        sp = pd.read_csv(sp_path, encoding='utf-8')

        if df.empty or sp.empty:
            print(f"[스킵] {quarter} → 데이터프레임이 비어 있음")
            continue

        # 병합
        merged = pd.merge(df, sp, on=['기준_년분기_코드', '행정동_코드', '행정동_코드_명'], how='outer')
        print(f"[{quarter}] 병합 완료 → 총 행 수: {len(merged)}")

        # 결측치 제거 당월매출금액이 NaN만
        merged_cleaned = merged.dropna(subset=['당월_매출_금액'])
        print(f"[{quarter}] 결측치 제거 후 행 수: {len(merged_cleaned)}")

        # 저장
        save_path = os.path.join(save_dir, f"서울_데이터_병합_{quarter}.csv")
        merged_cleaned.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"[{quarter}] 최종 저장 완료 → {save_path}")
