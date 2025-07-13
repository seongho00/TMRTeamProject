import time
import requests

KAKAO_API_KEY = "493573b251c629cab49ffc76ab14ea28"

# 주소 → 위도, 경도
def get_coords_from_address(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    documents = response.json().get("documents")
    if not documents:
        raise ValueError(f"주소 검색 실패: {address}")
    x = documents[0]["x"]
    y = documents[0]["y"]
    return x, y

# 위경도 → 행정동 코드(admiCd)
def get_admicode_from_coords(x, y):
    url = "https://dapi.kakao.com/v2/local/geo/coord2regioncode.json"
    headers = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}
    params = {"x": x, "y": y}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    documents = response.json().get("documents")
    for doc in documents:
        if doc["region_type"] == "H":
            return doc["code"]
    raise ValueError(f"행정동 코드 변환 실패: {x}, {y}")

# 전체 반복 실행 구조
def run_batch_for_dongs(dong_list):
    for dong in dong_list:
        try:
            print(f"[실행 중] {dong}")
            x, y = get_coords_from_address(dong)
            admi_cd = get_admicode_from_coords(x, y)
            print(f" - 위경도: ({x}, {y}) / admiCd: {admi_cd}")
            time.sleep(1.5)
        except Exception as e:
            print(f"[오류] {dong} 처리 중 문제 발생: {e}")
            time.sleep(5)

# 대전 행정동 리스트 예시
daejeon_dongs = [
    "대전광역시 동구 가양1동",
    "대전광역시 동구 가양2동",
    "대전광역시 동구 대동",
    "대전광역시 동구 성남동",
    "대전광역시 동구 효동",
    "대전광역시 서구 둔산1동",
    "대전광역시 서구 둔산2동",
    "대전광역시 서구 둔산3동",
    "대전광역시 중구 은행동",
    "대전광역시 중구 석교동",
    "대전광역시 유성구 봉명동",
    "대전광역시 유성구 온천1동",
    "대전광역시 대덕구 중리동",
    "대전광역시 대덕구 비래동",
]

# 위 경도만 불러오기
run_batch_for_dongs(daejeon_dongs)