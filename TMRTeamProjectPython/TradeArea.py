import requests

KAKAO_API_KEY = "493573b251c629cab49ffc76ab14ea28"
HEADERS = {"Authorization": f"KakaoAK {KAKAO_API_KEY}"}

# 업종 대분류 코드 매핑
major_category_codes = {
    "소매": "G2", "음식": "I2", "수리/개인": "S2",
    "과학/기술": "M1", "예체능": "R1", "교육": "P1",
    "부동산": "L1", "숙박": "I1", "보건의료": "Q1", "관리/임대": "N1"
}

# 주소 → 위도/경도 및 행정동 코드
def get_coords_from_address(address):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    params = {"query": address}
    res = requests.get(url, headers=HEADERS, params=params)
    res.raise_for_status()
    docs = res.json().get("documents", [])
    print(docs)
    if not docs:
        raise ValueError(f"[좌표 오류] {address}")

# 대분류 → 중분류 업종 리스트 요청
def get_mid_categories(major_code):
    url = "https://bigdata.sbiz.or.kr/gis/api/getTpbizMclCodeWithBest.json"
    params = {"tpbizLclcd": major_code}
    res = requests.get(url, params=params)
    res.raise_for_status()
    return res.json()

# 분석 번호 analyNo 요청
def get_analy_no(admiCd, upjongCd, address):
    url = "https://bigdata.sbiz.or.kr/gis/simpleAnls/getAvgAmtInfo.json"
    params = {
        "admiCd": admiCd,
        "upjongCd": upjongCd,
        "simpleLoc": address,
        "bizonNumber": "",
        "bizonName": "",
        "bzznType": "1",
        "xtLoginId": ""
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    return data.get("analyNo")

# 대전광역시 행정동 예시 리스트
daejeon_dongs = [
    "대전광역시 동구 효동"
]

for dong in daejeon_dongs:
    get_coords_from_address(dong)