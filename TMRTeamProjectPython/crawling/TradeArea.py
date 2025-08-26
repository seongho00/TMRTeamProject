import os
import random
import re
import time

import pymysql
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

success_list = []
error_list = []

download_path = r"C:\Users\user\Desktop\TeamProject\SimpAnly"
os.makedirs(download_path, exist_ok=True)

# Chrome 옵션 설정
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_path, # 다운로드 폴더
    "plugins.always_open_pdf_externally": True,  # PDF를 바로 다운로드
    "download.prompt_for_download": False,       # 다운로드 시 팝업 비활성화
    "safebrowsing.enabled": True
})
chrome_options.add_argument("--headless")  # 창 안 뜨게
chrome_options.add_argument("--disable-gpu")  # GPU 비활성화 (윈도우에서 headless 안정성)

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="1234",
    db="TMRTeamProject",
    charset="utf8mb4"
)
cursor = conn.cursor()

cursor.execute("SELECT * FROM admin_dong;")
dong_rows = cursor.fetchall()

cursor.execute("SELECT * FROM upjong_code;")
upjong_rows = cursor.fetchall()

for dong in dong_rows:
    admi_nm = dong[0]
    emd_cd = dong[1]
    emd_nm = dong[2]
    sgg_cd = dong[3]
    sgg_nm = dong[4]
    sido_nm = dong[6]

    simple_loc = f"{sido_nm} {sgg_nm} {emd_nm}"
    print(f"[동 시작] {simple_loc} ({emd_cd})")

    for upjong in upjong_rows:
        minor_cd = upjong[0]
        major_cd = upjong[1]
        middle_cd = upjong[3]
        middle_nm = upjong[4]
        minor_nm = upjong[5]

        try:
            headers = {
                "User-Agent": random.choice(USER_AGENTS),
                "Referer": "https://bigdata.sbiz.or.kr/"
            }

            # getAvgAmtInfo 요청
            avg_url = "https://bigdata.sbiz.or.kr/gis/simpleAnls/getAvgAmtInfo.json"
            params = {
                "admiCd": emd_cd,
                "upjongCd": minor_cd,
                "simpleLoc": simple_loc,
                "bizonNumber": "",
                "bizonName": "",
                "bzznType": "1",
                "xtLoginId": ""
            }
            avg_res = requests.get(avg_url, headers=headers, params=params, timeout=10)
            avg_res.raise_for_status()
            avg_data = avg_res.json()
            analyNo = avg_data.get("analyNo")
            mililis = avg_data.get("mililis")
            baeminStdYm = avg_data.get("baeminStdYm")
            baemin = avg_data.get("baemin")

            if not analyNo:
                raise Exception("analyNo 없음")

            # baemin 코드가 'Y'인것만 getBaeminInfo 요청
            if baemin == 'Y':
                baemin_url = "https://bigdata.sbiz.or.kr/gis/simpleAnls/getBaeminInfo.json"
                baemin_params = {
                    "admiCd": emd_cd,
                    "analyNo": analyNo,
                    "upjongCd": minor_cd,
                    "stdYm": baeminStdYm,
                    "mililis": mililis,
                    "dong": emd_nm,
                    "gu": sgg_nm,
                    "si": sido_nm,
                    "xtLoginId": ""
                }
                baemin_res = requests.get(baemin_url, headers=headers, params=baemin_params, timeout=10)
                baemin_res.raise_for_status()
                baemin_data = baemin_res.json()

                analyNo = baemin_data.get("analyNo")
                mililis = baemin_data.get("mililis")

            # getPopularInfo 요청
            popular_url = "https://bigdata.sbiz.or.kr/gis/simpleAnls/getPopularInfo.json"
            popular_params = {
                "analyNo": analyNo,
                "admiCd": emd_cd,
                "upjongCd": minor_cd,
                "mililis": mililis,
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
                print(f" → 성공: {minor_cd} 분석번호: {analy_no}")
            else:
                raise Exception("analyNo 없음")

            time.sleep(0.5)

            # 드라이버 실행
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(report_url)

            wait = WebDriverWait(driver, 5)

            # "저장" 버튼 클릭 (클래스: btnSAVEAS)
            try:
                # "저장" 버튼 클릭
                save_btn = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "btnSAVEAS")))
                save_btn.click()
                print("[1] 저장 버튼 클릭")

                confirm_button = WebDriverWait(driver, 5).until(
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

            # 현재 시각 기준
            download_started = time.time()

            # 다운로드 완료 후 파일 이름 변경
            timeout = 10
            while timeout > 0:
                files = [f for f in os.listdir(download_path) if f.endswith(".pdf")]
                if files:
                    files.sort(key=lambda f: os.path.getmtime(os.path.join(download_path, f)), reverse=True)
                    latest_file = files[0]
                    latest_path = os.path.join(download_path, latest_file)
                    file_mtime = os.path.getmtime(latest_path)

                    if not latest_file.endswith(".crdownload") and file_mtime >= download_started:
                        safe_filename = sanitize_filename(f"{simple_loc} {minor_nm}.pdf")
                        target_path = os.path.join(download_path, safe_filename)

                        if os.path.exists(target_path):
                            os.remove(target_path)

                        os.rename(latest_path, target_path)
                        print(f"[완료] {latest_file} → {safe_filename}")
                        break
                time.sleep(0.5)
                timeout -= 0.5

        except Exception as e:
            print(f" → 오류: {minor_cd}: {e}")
            error_list.append({
                "admiCd": emd_cd,
                "dongName": emd_nm,
                "upjongCd": minor_cd,
                "error": str(e)
            })
            time.sleep(1)

        finally:
            driver.quit()
