import requests
import pymysql
import pandas as pd
import time
import os
import random

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

success_list = []
error_list = []

download_path = os.path.join(os.path.expanduser("~"), "Downloads")

conn = pymysql.connect(
    host="localhost",
    user="root",
    password="",
    db="TMRTeamProject",
    charset="utf8mb4"
)
cursor = conn.cursor()

cursor.execute("SELECT * FROM admin_dong WHERE emd_nm = '효동';")
dong_rows = cursor.fetchall()

cursor.execute("SELECT minor_cd FROM upjong_code;")
upjong_rows = cursor.fetchall()

for dong in dong_rows:
    admi_cd = dong[5]
    sido_nm = dong[2]
    sgg_nm = dong[4]
    emd_nm = dong[6]
    simple_loc = f"{sido_nm} {sgg_nm} {emd_nm}"
    print(f"[동 시작] {simple_loc} ({admi_cd})")

    for upjong in upjong_rows:
        upjong_cd = upjong[0]

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

            mililis = avg_data.get("mililis")

            analyNo = avg_data.get("analyNo")
            print(analyNo)

            if not mililis:
                raise Exception("mililis 없음")

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

            df = pd.DataFrame(success_list)
            err_df = pd.DataFrame(error_list)

            df.to_csv(os.path.join(download_path, "analy_results.csv"), index=False, encoding="utf-8-sig")
            err_df.to_csv(os.path.join(download_path, "analy_errors.csv"), index=False, encoding="utf-8-sig")

            print("✅ 완료: Downloads 폴더에 analy_results.csv / analy_errors.csv 저장됨")

        except Exception as e:
            print(f"   → 오류: {upjong_cd}: {e}")
            error_list.append({
                "admiCd": admi_cd,
                "dongName": emd_nm,
                "upjongCd": upjong_cd,
                "error": str(e)
            })
            time.sleep(4)