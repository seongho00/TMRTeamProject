import os
import glob
import pandas as pd

# 데이터 폴더 리스트
df_dirs = {
    2022: "C:/Users/admin/Downloads/Seoul_data_2022",
    2023: "C:/Users/admin/Downloads/Seoul_data_2023",
    2024: "C:/Users/admin/Downloads/Seoul_data_2024",
    2025: "C:/Users/admin/Downloads/Seoul_data_2025",
}

# 병합 키
base_merge_key = ['기준_년분기_코드', '행정동_코드', '행정동_코드_명']
skip_columns = ['서비스_업종_코드', '서비스_업종_코드_명']
service_merge_key = base_merge_key + skip_columns

# 저장 폴더
save_dir = "C:/Users/admin/Downloads/Seoul_Merge_Data"
save_dir2 = "C:/Users/admin/Downloads/Seoul_Data_Special"
os.makedirs(save_dir, exist_ok=True)
os.makedirs(save_dir2, exist_ok=True)

def read_csv_safely(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path, encoding='utf-8')
    except UnicodeDecodeError:
        return pd.read_csv(path, encoding='cp949')

for year, year_dir in df_dirs.items():
    if year == 2022:
        quarters = [20221, 20222, 20223, 20224]
    elif year == 2023:
        quarters = [20231, 20232, 20233, 20234]
    elif year == 2024:
        quarters = [20241, 20242, 20243, 20244]
    elif year == 2025:
        quarters = [20251]

    csv_files = glob.glob(os.path.join(year_dir, "*.csv"))

    for quarter in quarters:
        base_df = None
        service_df = None

        for file_path in csv_files:
            try:
                df = read_csv_safely(file_path)

                if '기준_년분기_코드' not in df.columns:
                    print(f"[스킵] {os.path.basename(file_path)} → 기준_년분기_코드 없음")
                    continue

                # 키 컬럼 형 변환
                df['기준_년분기_코드'] = df['기준_년분기_코드'].astype(str)
                if '행정동_코드' in df.columns:
                    df['행정동_코드'] = df['행정동_코드'].astype(str)

                df_q = df[df['기준_년분기_코드'] == str(quarter)].copy()
                if df_q.empty:
                    print(f"[스킵] {os.path.basename(file_path)} → 분기 {quarter} 데이터 없음")
                    continue

                if '행정동_코드_명' not in df_q.columns:
                    print(f"[스킵] {os.path.basename(file_path)} → 행정동_코드_명 없음")
                    continue

                # 특정 동 제외
                df_q = df_q[df_q['행정동_코드_명'] != '둔촌1동']

                has_service_cols = all(col in df_q.columns for col in skip_columns)

                # -------- 일반 병합 --------
                if not has_service_cols:
                    if base_df is None:
                        base_df = df_q
                        print(f"[초기화-일반] {os.path.basename(file_path)} | rows: {len(df_q)}")
                    else:
                        merge_keys = [k for k in base_merge_key if k in base_df.columns and k in df_q.columns]
                        if not merge_keys:
                            print(f"[스킵-일반] {os.path.basename(file_path)} → 병합 키 없음")
                            continue

                        # 중복 컬럼 제거(키 제외)
                        drop_cols = [col for col in df_q.columns if col in base_df.columns and col not in merge_keys]
                        if drop_cols:
                            df_q = df_q.drop(columns=drop_cols)

                        base_df = pd.merge(base_df, df_q, on=merge_keys, how='outer')

                # -------- 서비스 병합 --------
                else:
                    if service_df is None:
                        service_df = df_q
                        print(f"[초기화-서비스] {os.path.basename(file_path)} | rows: {len(df_q)}")
                    else:
                        merge_keys = [k for k in service_merge_key if k in service_df.columns and k in df_q.columns]
                        if not merge_keys:
                            print(f"[스킵-서비스] {os.path.basename(file_path)} → 병합 키 없음")
                            continue

                        drop_cols = [col for col in df_q.columns if col in service_df.columns and col not in merge_keys]
                        if drop_cols:
                            df_q = df_q.drop(columns=drop_cols)

                        service_df = pd.merge(service_df, df_q, on=merge_keys, how='outer')

            except Exception as e:
                print(f"[에러] 병합 실패: {os.path.basename(file_path)} | {e}")

        # 저장
        if base_df is not None:
            out1 = os.path.join(save_dir, f"서울_상권분석_행정동_{quarter}.csv")
            base_df.to_csv(out1, index=False, encoding='utf-8-sig')
            print(f"[완료] {quarter}분기 일반 병합 → {out1}")

        if service_df is not None:
            out2 = os.path.join(save_dir2, f"서울_상권분석_서비스업종포함_행정동_{quarter}.csv")
            service_df.to_csv(out2, index=False, encoding='utf-8-sig')
            print(f"[완료] {quarter}분기 서비스 병합 → {out2}")
