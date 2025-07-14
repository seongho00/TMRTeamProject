import requests
import pymysql
import time
import os
import random
import re

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

success_list = []
error_list = []

download_path = r"C:\Users\user\Desktop\TeamProject\data"
os.makedirs(download_path, exist_ok=True)

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_path,  # 다운로드 폴더
    "plugins.always_open_pdf_externally": True,  # PDF를 바로 다운로드
    "download.prompt_for_download": False,       # 다운로드 시 팝업 비활성화
    "safebrowsing.enabled": True
})
chrome_options.add_argument("--headless")  # 창 안 뜨게
chrome_options.add_argument("--disable-gpu")  # GPU 비활성화 (윈도우에서 headless 안정성)

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    db="TMRTeamProject",
    charset="utf8mb4"
)
cursor = conn.cursor()

cursor.execute("SELECT * FROM admin_dong ORDER BY emd_cd DESC;")
dong_rows = cursor.fetchall()

cursor.execute("SELECT * FROM upjong_code;")
upjong_rows = cursor.fetchall()

for dong in dong_rows:
    admi_cd = dong[5]
    sido_nm = dong[2]
    sgg_nm = dong[4]
    emd_nm = dong[6]
    simple_loc = f"{sido_nm} {sgg_nm} {emd_nm}"
    print(f"[동 시작] {simple_loc} ({admi_cd})")

    for upjong in upjong_rows:
        upjong_cd = upjong[4]
        minor_nm = upjong[5]
        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Referer": "https://bigdata.sbiz.or.kr/"
            }

            params = {
                "admiCd": admi_cd,
                "upjongCd": upjong_cd,
                "simpleLoc": simple_loc,
                "bizonNumber": "",
                "bizonName": "",
                "bzznType": "1",
                "xtLoginId": ""
            }

            avg_url = "https://bigdata.sbiz.or.kr/gis/simpleAnls/getAvgAmtInfo.json"
            avg_res = requests.get(avg_url, headers=headers, params=params, timeout=10)
            avg_res.raise_for_status()
            avg_data = avg_res.json()
            analyNo = avg_data.get("analyNo")
            print(analyNo)

            popular_url = "https://bigdata.sbiz.or.kr/gis/simpleAnls/getPopularInfo.json"
            popular_params = {
                "analyNo": analyNo,
                "admiCd": admi_cd,
                "upjongCd": upjong_cd,
                "bizonNumber": "",
                "bizonName": "",
                "bzznType": "1",
                "xtLoginId": ""
            }

            popular_res = requests.get(popular_url, headers=headers, params=popular_params, timeout=10)
            popular_res.raise_for_status()
            popular_data = popular_res.json()

            analy_no = popular_data.get("analyNo")

            if analy_no:
                report_url = f"https://bigdata.sbiz.or.kr/gis/report/viewer.sg?reportId={analy_no}"
                print(f"   → 성공: {upjong_cd} 분석번호: {analy_no}")
                success_list.append({
                    "admiCd": admi_cd,
                    "dongName": emd_nm,
                    "upjongCd": upjong_cd,
                    "analyNo": analy_no,
                    "url": report_url
                })
            else:
                raise Exception("analyNo 없음")

            time.sleep(0.5)

            # 드라이버 실행
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(report_url)

            wait = WebDriverWait(driver, 3)

            # "저장" 버튼 클릭 (클래스: btnSAVEAS)
            try:
                # "저장" 버튼 클릭
                save_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnSAVEAS")))
                save_btn.click()
                print("[1] 저장 버튼 클릭")

                confirm_button = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[3]/div/button[2]"))
                )
                confirm_button.click()
                print("저장 성공")
            except Exception as e:
                print("저장 버튼 클릭 실패:", e)

            new_filename = f"{simple_loc} {minor_nm}.pdf"

            # 파일명에 사용 불가능한 문자 제거 함수
            def sanitize_filename(name):
                return re.sub(r'[\\/:*?"<>|]', '_', name)

            # 6. 다운로드 완료 후 파일 이름 변경
            timeout = 30
            while timeout > 0:
                files = [f for f in os.listdir(download_path) if f.endswith(".pdf")]
                if files:
                    files.sort(key=lambda f: os.path.getmtime(os.path.join(download_path, f)), reverse=True)
                    latest_file = files[0]
                    latest_path = os.path.join(download_path, latest_file)
                    if not latest_file.endswith(".crdownload"):
                        # 유효한 파일명으로 변환
                        safe_filename = sanitize_filename(new_filename)
                        target_path = os.path.join(download_path, safe_filename)
                        if os.path.exists(target_path):
                            os.remove(target_path)
                        os.rename(latest_path, target_path)
                        print(f"[완료] {latest_file} → {safe_filename}")
                        break
                time.sleep(1)
                timeout -= 1

        except Exception as e:
            print(f"   → 오류: {upjong_cd}: {e}")
            error_list.append({
                "admiCd": admi_cd,
                "dongName": emd_nm,
                "upjongCd": upjong_cd,
                "error": str(e)
            })
            time.sleep(4)
