import requests
import pandas as pd

SPRING_URL = "http://localhost:8080/usr/learn/savedDB"

def df_to_json(df):
    return [
        {
            "hjdCo": str(r.get("행정동_코드", "")),
            "hjdCn": str(r.get("행정동_코드_명", "")),
            "serviceCode": str(r.get("서비스_업종_코드", "")),
            "serviceName": str(r.get("서비스_업종_명", "")),
            "riskScore": None if pd.isna(r.get("위험도_점수")) else float(r["위험도_점수"]),
            "risk3": None if pd.isna(r.get("위험도")) else int(r["위험도"]),
            "risk7": None if pd.isna(r.get("위험도7")) else str(r["위험도7"]),
            "predictedRisk": None if pd.isna(r.get("예측_위험도")) else int(r["예측_위험도"]),
            "cluster": None if pd.isna(r.get("cluster")) else int(r["cluster"]),
        }
        for _, r in df.iterrows()
    ]

def send_to_server(df: pd.DataFrame):
    # DataFrame을 스프링 서버로 전송
    json_data = df_to_json(df)
    resp = requests.post(SPRING_URL, json=json_data)
    if resp.status_code == 200:
        print(f"✅ 전송 성공: {len(json_data)}건 저장됨")
    else:
        print(f"❌ 전송 실패: {resp.status_code}, {resp.text}")
