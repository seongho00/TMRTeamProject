import geopandas as gpd

# 1. 파일 경로 설정 (압축 해제된 .shp 파일 경로)
shp_path = "C:/Users/admin/Desktop/bnd_dong_25_2024_2Q/bnd_dong_25_2024_2Q.shp"  # 실제 경로로 수정

# 2. SHP 파일 읽기 (관련된 .shx, .dbf, .prj 자동으로 함께 사용됨)
gdf = gpd.read_file(shp_path)

# 3. 좌표계 WGS84 (EPSG:4326)로 변환 (웹 지도 호환용)
gdf = gdf.to_crs(epsg=4326)

# 4. GeoJSON으로 저장
output_path = "../../src/main/resources/templates/daejeon_emds.geojson"
gdf.to_file(output_path, driver="GeoJSON")

print(f"✅ GeoJSON 변환 완료 → {output_path}")
