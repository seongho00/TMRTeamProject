import requests
import pandas as pd
from tqdm import tqdm
import time

# --- 설정 ---
BASE_URL = "https://new.land.naver.com/api/regions/list?cortarNo="
OUTPUT_FILENAME = "../src/main/resources/hangjeongdong_code_final.csv"

# 요청 시 차단을 피하기 위한 헤더
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://new.land.naver.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
}

def get_region_list(cortar_code):
    """지정된 코드로 하위 지역 목록을 가져오는 함수"""
    try:
        response = requests.get(f"{BASE_URL}{cortar_code}", headers=HEADERS, timeout=10)
        response.raise_for_status()
        data = response.json()

        # 데이터가 {'regionList': [...]} 형태로 감싸져 있는지 확인하고 내용물만 꺼냄
        if isinstance(data, dict) and 'regionList' in data:
            return data['regionList']
        return data

    except requests.exceptions.JSONDecodeError:
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"  [오류] 코드 {cortar_code} 요청 실패: {e}")
        return None

def main():
    """메인 실행 함수"""
    print("네이버 부동산 지역 코드 수집을 시작합니다.")
    final_results = []

    # 1. 시/도 목록 가져오기
    sido_list = get_region_list("0000000000")

    if not isinstance(sido_list, list):
        print(f"\n[오류] 최상위 지역 목록을 가져오는 데 실패했습니다.")
        print(f"  (수신 내용: {sido_list})")
        return

    print(f"총 {len(sido_list)}개의 시/도를 발견했습니다.")

    # 2. 각 시/도에 대해 시/군/구 목록 가져오기
    for sido in tqdm(sido_list, desc="시/군/구 수집 중"):
        sido_name = sido['cortarName']
        sido_code = sido['cortarNo']
        time.sleep(0.1)

        sigungu_list = get_region_list(sido_code)
        if not isinstance(sigungu_list, list): continue

        # 3. 각 시/군/구에 대해 읍/면/동 목록 가져오기
        for sigungu in sigungu_list:
            sigungu_name = sigungu['cortarName']
            sigungu_code = sigungu['cortarNo']
            time.sleep(0.1)

            dong_list = get_region_list(sigungu_code)
            if not isinstance(dong_list, list):
                if '읍면동' in sigungu_name or sigungu_name.endswith(('읍', '면', '동')):
                    final_results.append({
                        "sido_name": sido_name,
                        "sigungu_name": "",
                        "adm_dong_name": sigungu_name,
                        "full_code": sigungu_code
                    })
                continue

            # 4. 최종 결과에 읍/면/동 정보 추가
            for dong in dong_list:
                final_results.append({
                    "sido_name": sido_name,
                    "sigungu_name": sigungu_name,
                    "adm_dong_name": dong['cortarName'],
                    "full_code": dong['cortarNo']
                })

    if not final_results:
        print("수집된 데이터가 없습니다. 네트워크 상태를 확인 후 다시 시도해 주세요.")
        return

    # 5. 수집된 데이터를 CSV 파일로 저장
    df = pd.DataFrame(final_results)
    df.to_csv(OUTPUT_FILENAME, index=False, encoding='utf-8-sig')

    print(f"\n✅ 성공! '{OUTPUT_FILENAME}' 파일이 생성되었습니다.")
    print(f"   (총 {len(df)}개의 읍/면/동 정보 포함)")

    print("\n--- 생성된 파일 미리보기 (상위 5개) ---")
    print(df.head())
    print("------------------------------------")


if __name__ == "__main__":
    main()