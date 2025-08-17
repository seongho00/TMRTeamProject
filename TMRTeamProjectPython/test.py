import requests, urllib.parse
from pyproj import Transformer

VWORLD_KEY = "0D1E185A-F71A-3D74-AE65-579E01CC79CD"

def geocode_roadaddr(addr: str):
    url = "https://api.vworld.kr/req/address"
    params = {
        "service": "address",
        "request": "getcoord",
        "format": "json",
        "crs": "EPSG:4326",  # 위경도(Lon/Lat)
        "key": VWORLD_KEY,
        "type": "road",      # 도로명 주소라면 'road', 지번이면 'parcel'
        "address": addr
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if data.get("response", {}).get("status") != "OK":
        raise ValueError(f"Geocode 실패: {data}")
    p = data["response"]["result"]["point"]
    lon, lat = float(p["x"]), float(p["y"])
    return lon, lat

# EPSG:4326 -> EPSG:5179 (Korea 2000 / Central Belt)
to_5179 = Transformer.from_crs(4326, 5179, always_xy=True)
# EPSG:4326 -> EPSG:5186 (TM중부)
to_5186 = Transformer.from_crs(4326, 5186, always_xy=True)

def convert_coords(lon, lat):
    x5179, y5179 = to_5179.transform(lon, lat)
    x5186, y5186 = to_5186.transform(lon, lat)
    return (x5179, y5179), (x5186, y5186)

# ▼ 예시: 주소 배열(소각장 주소/시설명에 맞게 넣어주세요)
addresses = [
    "서울특별시 마포구 하늘공원로 86",   # 마포자원회수시설(예시)
    "서울특별시 강남구 남부순환로 3318", # 강남자원회수시설(예시)
    "서울특별시 양천구 목동서로 155",  # 양천(예시) - 실제 주소 확인 후 사용
    "서울특별시 노원구 공릉로20길 17"       # 노원(예시) - 실제 주소 확인 후 사용
]

for addr in addresses:
    lon, lat = geocode_roadaddr(addr)
    (x5179, y5179), (x5186, y5186) = convert_coords(lon, lat)
    print(f"[{addr}]")
    print(f"  EPSG:4326  lon,lat = {lon:.6f}, {lat:.6f}")
    print(f"  EPSG:5179  x,y     = {x5179:.3f}, {y5179:.3f}")
    print(f"  EPSG:5186  x,y     = {x5186:.3f}, {y5186:.3f}")
