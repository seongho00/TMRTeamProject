import os

import pandas as pd
import geopandas as gpd
import folium
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans

os.environ["OMP_NUM_THREADS"] = "2"

plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False

# 1. SHP 파일 불러오기
gdf = gpd.read_file("C:/Users/user/Downloads/서울시 상권분석서비스(영역-행정동)/서울시 상권분석서비스(영역-행정동).shp", encoding='utf-8')

# 2. CSV 파일 불러오기
df = pd.read_csv("C:/Users/user/Downloads/유동인구_매출_분석결과_20241.csv", encoding='utf-8-sig')

# 3. 병합
df['행정동_코드'] = df['행정동_코드'].astype(str)
gdf['adm_cd'] = gdf['ADSTRD_CD'].astype(str)
merged = gdf.merge(df, left_on='adm_cd', right_on='행정동_코드')

# 4. KMeans 클러스터링 (매출 기준 5등급)
kmeans = KMeans(n_clusters=5, random_state=42)
merged['매출_클러스터'] = kmeans.fit_predict(merged[['당월_총_매출_금액']])

# 5. 클러스터 → 등급 (1~5, 높은 매출일수록 높은 등급)
merged['매출_등급'] = merged['매출_클러스터'].rank(method='dense').astype(int)

# 6. 색상 매핑 (연노랑 -> 빨강)
colors = {
    1: '#ffffb2',
    2: '#fecc5c',
    3: '#fd8d3c',
    4: '#f03b20',
    5: '#bd0026'
}
merged['color'] = merged['매출_등급'].map(colors)

# WGS84 (EPSG:4326)로 변환
merged_wgs84 = merged.to_crs(epsg=4326)

# 12. GeoJSON으로 저장
merged_wgs84.to_file("seoul_area_level.geojson", driver="GeoJSON", encoding="utf-8")

# 7. 정적 시각화
merged.plot(column='매출_등급', cmap='OrRd', legend=True, edgecolor='black')
plt.title('2024년 1분기 행정동별 매출 등급')
plt.axis('off')
plt.tight_layout()
plt.show()

# 8. Folium 지도 생성
center = [37.5665, 126.9780]
m = folium.Map(location=center, zoom_start=11)

# 9. GeoJson으로 등급별 색상 시각화
def style_function(feature):
    adm_cd = feature['properties']['adm_cd']
    color = merged.loc[merged['adm_cd'] == adm_cd, 'color'].values[0]
    return {
        'fillColor': color,
        'color': 'black',
        'weight': 0.5,
        'fillOpacity': 0.7,
    }

folium.GeoJson(
    merged,
    name='행정동',
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=['adm_cd', '매출_등급', '당월_총_매출_금액', '총_유동인구_수'],
        aliases=['행정동_코드', '매출등급', '매출액', '유동인구'],
        localize=True
    )
).add_to(m)

# 10. 팝업 정보 추가
for _, row in merged.iterrows():
    if row['geometry'].geom_type == 'Polygon':
        center_point = row['geometry'].centroid.coords[0][::-1]
        popup_text = f"""
        <b>행정동코드:</b> {row['adm_cd']}<br>
        <b>매출 등급:</b> {row['매출_등급']}<br>
        <b>총 유동인구:</b> {int(row['총_유동인구_수'])}<br>
        <b>당월 매출액:</b> {int(row['당월_총_매출_금액'])}
        """
        folium.Marker(center_point, popup=popup_text).add_to(m)

m.save("soul_area.html")
