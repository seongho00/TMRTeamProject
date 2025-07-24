import pandas as pd
import os
import zipfile


# ZIP 파일 경로
folder_path = 'C:/Users/admin/Desktop/팀플 자료/서울 생활인구'
output_folder = "C:/Users/admin/Desktop/서울 데이터 결과"

os.makedirs(output_folder, exist_ok=True)

for mm in range(1, 13):
    ym = f'2024{mm:02d}'
    local_file = f'LOCAL_PEOPLE_DONG_{ym}.zip'
    foreigner_file = f'LONG_FOREIGNER_DONG_{ym}.zip'

    local_path = os.path.join(folder_path, local_file)
    foreigner_path = os.path.join(folder_path, foreigner_file)

    if not os.path.exists(local_path) or not os.path.exists(foreigner_path):
        print(f"❌ 파일 없음: {local_file} 또는 {foreigner_file}")
        continue

    # 1. 파일 열기 (절대 reset_index 하지 마세요)
    with zipfile.ZipFile(local_path, 'r') as z1:
        local_csv = [f for f in z1.namelist() if f.endswith('.csv')][0]
        with z1.open(local_csv) as f1:
            df_local = pd.read_csv(f1, encoding='utf-8-sig', index_col=False)  # ✅ 인덱스로 쓰지마!
            df_local.columns = df_local.columns.str.strip().str.replace('"', '')


    # 외국인 데이터 읽기
    with zipfile.ZipFile(foreigner_path, 'r') as z2:
        foreigner_csv = [f for f in z2.namelist() if f.endswith('.csv')][0]
        with z2.open(foreigner_csv) as f2:
            df_foreigner = pd.read_csv(f2, encoding='utf-8-sig', index_col=False)
            df_foreigner.columns = df_foreigner.columns.str.strip().str.replace('"', '')

    # 기준 컬럼 숫자형 변환 (병합 안정성 확보)
    df_local['기준일ID'] = pd.to_numeric(df_local['기준일ID'], errors='coerce')
    df_foreigner['기준일ID'] = pd.to_numeric(df_foreigner['기준일ID'], errors='coerce')

    # 병합
    merged_df = pd.merge(
        df_local,
        df_foreigner,
        on=['기준일ID', '시간대구분', '행정동코드'],
        how='left'
    )

    # NaN 채우고 총생활인구수 합산
    merged_df['총생활인구수_x'] = merged_df['총생활인구수_x'].fillna(0)
    merged_df['총생활인구수_y'] = merged_df['총생활인구수_y'].fillna(0)
    merged_df['총생활인구수'] = merged_df['총생활인구수_x'] + merged_df['총생활인구수_y']
    merged_df.drop(columns=['총생활인구수_x', '총생활인구수_y'], inplace=True)

    # 저장
    output_file = os.path.join(output_folder, f"서울_생활인구_병합_{ym}.csv")
    merged_df.to_csv(output_file, index=False, encoding="utf-8-sig")
    print(f"✅ 저장 완료: {output_file}")