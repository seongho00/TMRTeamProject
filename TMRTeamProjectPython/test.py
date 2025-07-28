import pandas as pd
import geopandas as gpd
import folium
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Malgun Gothic'  # 윈도우용 한글 폰트
plt.rcParams['axes.unicode_minus'] = False     # 마이너스 깨짐 방지

# 1. SHP 파일 불러오기
gdf = gpd.read_file("C:/Users/user/Downloads/서울시 상권분석서비스(영역-행정동)/서울시 상권분석서비스(영역-행정동).shp", encoding='utf-8')

# 2. CSV 기반 데이터 불러오기
df = pd.read_csv("C:/Users/user/Downloads/유동인구_매출_분석결과_2024_1분기.csv", encoding='utf-8-sig')  # '행정동코드', '생활인구', '유동인구', '매출액'

print(gdf)
# 3. 컬럼 이름 정리 및 병합
df['행정동코드'] = df['행정동코드'].astype(str)
gdf['adm_cd'] = gdf['ADSTRD_CD'].astype(str)
merged = gdf.merge(df, left_on='adm_cd', right_on='행정동코드')

# 4. 정적 시각화 (matplotlib)
plt.figure(figsize=(10, 8))
merged.plot(column='당월_매출_금액', cmap='OrRd', legend=True, edgecolor='black')
plt.title('2024년 1분기 행정동별 매출액 시각화')
plt.axis('off')
plt.tight_layout()
plt.show()

# 5. Folium 지도 생성
center = [37.5665, 126.9780]  # 서울 중심 좌표
m = folium.Map(location=center, zoom_start=11)

# 6. Choropleth (단계구분도)
folium.Choropleth(
    geo_data=merged,
    data=merged,
    columns=['adm_cd', '당월_매출_금액'],
    key_on='feature.properties.adm_cd',
    fill_color='YlOrRd',
    fill_opacity=0.7,
    line_opacity=0.3,
    legend_name='2024년 1분기 매출액',
).add_to(m)

# 7. 행정동별 팝업 정보 추가
for _, row in merged.iterrows():
    if row['geometry'].geom_type == 'Polygon':
        center_point = row['geometry'].centroid.coords[0][::-1]  # (lat, lon)
        popup_text = f"""
        <b>행정동코드:</b> {row['adm_cd']}<br>
        <b>유동인구:</b> {int(row['총_유동인구_수'])}<br>
        <b>매출액:</b> {int(row['당월_매출_금액'])}
        """
        folium.Marker(center_point, popup=popup_text).add_to(m)

    folium.GeoJson(
        merged,
        name='행정동',
        tooltip=folium.GeoJsonTooltip(fields=['adm_cd'], aliases=['행정동명:'])
    ).add_to(m)

# 8. HTML 저장
m.save("서울_상권_시각화.html")
