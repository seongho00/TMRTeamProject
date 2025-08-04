import os

import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

os.environ["OMP_NUM_THREADS"] = "2"

# 한글 폰트
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# SHP 파일 불러오기
shp_path = "C:/Users/user/Downloads/서울시 상권분석서비스(영역-행정동)/서울시 상권분석서비스(영역-행정동).shp"
gdf = gpd.read_file(shp_path, encoding='utf-8')
gdf['adm_cd'] = gdf['ADSTRD_CD'].astype(str)

# 분기별 CSV 파일 불러오기
csv_paths = [
    ("C:/Users/user/Downloads/유동인구_매출_분석결과_20241.csv", 20241),
    ("C:/Users/user/Downloads/유동인구_매출_분석결과_20242.csv", 20242),
    ("C:/Users/user/Downloads/유동인구_매출_분석결과_20243.csv", 20243),
    ("C:/Users/user/Downloads/유동인구_매출_분석결과_20244.csv", 20244),
]

dfs = []
for path, quarter in csv_paths:
    df = pd.read_csv(path)
    df['기준_분기'] = quarter
    df['행정동_코드'] = df['행정동_코드'].astype(str)
    dfs.append(df)

full_df = pd.concat(dfs, ignore_index=True)

# 상관계수 및 위험도 점수 계산
results = []
grouped = full_df.groupby(['행정동_코드', '행정동_코드_명'])

for (code, name), group in grouped:
    if len(group) >= 2 and group['총_유동인구_수'].std() != 0 and group['당월_총_매출_금액'].std() != 0:
        corr = group['총_유동인구_수'].corr(group['당월_총_매출_금액'])
        score = 1 - corr if pd.notnull(corr) else None
        results.append({
            '행정동_코드': code,
            '행정동_코드_명': name,
            '상관계수': corr,
            '상관_위험도점수': score
        })

cor_df = pd.DataFrame(results)
cor_df['행정동_코드'] = cor_df['행정동_코드'].astype(str)
cor_df['위험등급'] = pd.qcut(cor_df['상관_위험도점수'], q=5, labels=[1, 2, 3, 4, 5])

# 병합
merged = gdf.merge(cor_df, left_on='adm_cd', right_on='행정동_코드')

# 색상 매핑
colors = {
    1: '#2ca25f',
    2: '#99d8c9',
    3: '#fdbb84',
    4: '#fc8d59',
    5: '#e34a33'
}
merged['color'] = merged['위험등급'].map(colors)

# 좌표계 변환
merged = merged.to_crs(epsg=4326)
merged.to_file("C:/Users/user/Desktop/TeamProject/TMRTeamProject/src/main/resources/static/js/seoul_area_level.geojson", driver="GeoJSON", encoding='utf-8')

# 시각화
merged.plot(
    column='위험등급',
    cmap='RdYlGn_r',  # 높은 등급(위험)일수록 붉은색
    legend=True,
    edgecolor='black'
)
plt.title("행정동별 상관 기반 위험등급 (2024년 1~4분기)", fontsize=15)
plt.axis("off")
plt.tight_layout()
plt.show()
