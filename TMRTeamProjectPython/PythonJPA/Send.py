import numpy as np
import pandas as pd
import requests

SPRING_URL = "http://localhost:8080/usr/learn/savedDB"

def _str_or_empty(x):
    # NaN -> "", 그 외 문자열화
    if x is None:
        return ""
    try:
        if isinstance(x, float) and np.isnan(x):
            return ""
    except Exception:
        pass
    return str(x)

def _float_or_none(x):
    # NaN/inf/변환불가 -> None (JSON 호환)
    try:
        v = float(x)
        if np.isfinite(v):
            return v
        return None
    except Exception:
        return None

def _int_or_none(x):
    # NaN/빈문자/변환불가 -> None
    try:
        if x is None:
            return None
        if isinstance(x, float) and (np.isnan(x) or not np.isfinite(x)):
            return None
        # 먼저 int 시도, 실패 시 float->int 시도
        try:
            return int(x)
        except Exception:
            return int(float(x))
    except Exception:
        return None

def df_to_json(df: pd.DataFrame):
    # 직렬화 전에 NaN/inf를 통일
    df = df.replace([np.inf, -np.inf], np.nan)

    rows = []
    for _, r in df.iterrows():
        rows.append({
            "hjdCo":              _str_or_empty(r.get("행정동_코드")),
            "hjdCn":              _str_or_empty(r.get("행정동_코드_명")),
            "serviceTypeCode":    _str_or_empty(r.get("서비스_업종_코드")),
            "serviceTypeName":    _str_or_empty(r.get("서비스_업종_코드_명")),
            "riskScore":          _float_or_none(r.get("위험도_점수")),
            "riskLevel":          _str_or_empty(r.get("위험도_단계")) or None,
            "riskLabel":          _int_or_none(r.get("실제_위험도")),
            "predictedRiskLabel": _int_or_none(r.get("예측_위험도")),
            "predictedConfidence":_float_or_none(r.get("예측_신뢰도")),
            "risk100All":         _float_or_none(r.get("risk100_all")),
            "risk100ByBiz":       _float_or_none(r.get("risk100_by_biz")),
        })
    return rows

def send_to_server(df: pd.DataFrame):
    # 혹시 모를 NaN/inf를 먼저 정리
    df = df.replace([np.inf, -np.inf], np.nan)

    payload = df_to_json(df)
    resp = requests.post(SPRING_URL, json=payload)

    if resp.status_code == 200:
        print(f"전송 성공 O: {len(payload)}건 저장됨")
    else:
        print(f"전송 실패 X: {resp.status_code}\n{resp.text}")
