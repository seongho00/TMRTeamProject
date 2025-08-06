import glob
import os

import pandas as pd

df_dir = "C:/Users/user/Downloads/Seoul_data"
file_list = glob.glob(os.path.join(df_dir, "*.csv"))

base_merge_key = ['기준_년분기_코드', '행정동_코드', '행정동_코드_명']
skip_columns = ['서비스_업종_코드', '서비스_업종_코드_명']
service_merge_key = base_merge_key + skip_columns

for quarter in [20241, 20242, 20243, 20244]:
    base_df = None
    service_df = None

    for file_path in file_list:
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
            df['기준_년분기_코드'] = df['기준_년분기_코드'].astype(str)

            df_q = df[df['기준_년분기_코드'] == str(quarter)].copy()
            df_q = df_q[df_q['행정동_코드_명'] != '둔촌1동']

            has_service_cols = all(col in df_q.columns for col in skip_columns)

            # 서비스 업종 코드 없는 파일 → 일반 병합
            if not has_service_cols:
                if base_df is None:
                    base_df = df_q
                else:
                    merge_keys = [k for k in base_merge_key if k in base_df.columns and k in df_q.columns]
                    if not merge_keys:
                        print(f"일반 병합 스킵: {file_path} (병합 키 없음)")
                        continue
                    base_df = pd.merge(base_df, df_q, on=merge_keys, how='inner')

            # 서비스 업종 코드 있는 파일 → 따로 병합
            else:
                if service_df is None:
                    service_df = df_q
                else:
                    merge_keys = [k for k in service_merge_key if k in service_df.columns and k in df_q.columns]
                    if not merge_keys:
                        print(f"서비스 병합 스킵: {file_path} (병합 키 없음)")
                        continue
                    service_df = pd.merge(service_df, df_q, on=merge_keys, how='inner')

        except Exception as e:
            print(f"병합 실패: {file_path} | 오류: {e}")

    # 저장 폴더 생성
    save_dir = "C:/Users/user/Downloads/Seoul_Merge_Data"
    os.makedirs(save_dir, exist_ok=True)

    save_dir2 = "C:/Users/user/Downloads/Seoul_Data_Special"
    os.makedirs(save_dir2, exist_ok=True)

    # 일반 데이터 저장
    if base_df is not None:
        save_path = os.path.join(save_dir, f"서울_상권분석_행정동_{quarter}.csv")
        base_df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"{quarter}분기 일반 병합 완료: {save_path}")

    # 서비스 업종 포함 데이터 저장
    if service_df is not None:
        save_path = os.path.join(save_dir2, f"서울_상권분석_서비스업종포함_행정동_{quarter}.csv")
        service_df.to_csv(save_path, index=False, encoding='utf-8-sig')
        print(f"{quarter}분기 서비스 병합 완료: {save_path}")
