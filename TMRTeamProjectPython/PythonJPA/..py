import datetime as dt
import json
import math
import os
import time
import traceback

import numpy as np
import pandas as pd
import requests

# ======== 전역 설정(네 환경에 맞게 수정) ========
API_URL = "http://localhost:8080/api/risk/predictions/bulk"  # 서버 수신 endpoint
API_TOKEN = None  # 토큰 있으면 "xxxx" 형태로 입력
TIMEOUT = 30      # 요청 타임아웃(초)
CHUNK_SIZE = 20000  # 청크 사이즈(행 수)
RETRIES = 3       # 실패 시 재시도 횟수
WAIT = 2.0        # 재시도 사이 대기(초)
BACKUP_DIR = r"C:/Users/admin/Downloads/Seoul_RandomForest"  # 실패 시 백업 폴더

# ======== 컬럼 매핑(한글 → 서버 필드명) 필요에 맞게 수정 ========
COLUMN_MAP = {
    '행정동_코드': 'emd_cd',
    '행정동_코드_명': 'emd_nm',
    '서비스_업종_코드': 'svc_ind_cd',
    '서비스_업종_코드_명': 'svc_ind_nm',
    '기준_년분기_코드': 'quarter',
    '실제_위험도': 'actual_risk5',
    '예측_위험도': 'pred_risk5',
    '예측_신뢰도': 'pred_conf',
    '위험도_점수': 'risk_score',
    '위험도_단계': 'risk_quantile5',
    '예측_위험도_다음분기': 'next_pred_risk5',
    '예측_위험도_다음분기_라벨': 'next_pred_risk5_label',
    '예측_신뢰도_다음분기': 'next_pred_conf'
}

# ======== 유틸: DataFrame → JSON 직렬화 보조 ========
def _df_prepare(df: pd.DataFrame) -> pd.DataFrame:
    """카테고리/NaN/넘파이 타입을 서버에 보내기 좋게 정리"""
    df = df.copy()
    # 카테고리는 문자열로
    for c in df.select_dtypes(include=['category']).columns:
        df[c] = df[c].astype(str)
    # 타임스탬프는 ISO 문자열로
    for c in df.columns:
        if np.issubdtype(df[c].dtype, np.datetime64):
            df[c] = pd.to_datetime(df[c]).dt.strftime("%Y-%m-%dT%H:%M:%S")
    # NaN → None
    df = df.where(pd.notnull(df), None)
    return df

def _apply_column_map(df: pd.DataFrame, col_map: dict) -> pd.DataFrame:
    """컬럼명 매핑 적용(서버 스키마와 맞추기)"""
    df = df.copy()
    # 존재하는 컬럼만 매핑
    rename_map = {k: v for k, v in col_map.items() if k in df.columns}
    return df.rename(columns=rename_map)

def _to_records(df: pd.DataFrame) -> list:
    """DataFrame → list[dict]"""
    # 넘파이 타입을 파이썬 기본형으로 바꿔서 JSON 직렬화 안전하게
    def _cast(v):
        if isinstance(v, (np.integer, np.int64, np.int32, np.int16, np.int8)):
            return int(v)
        if isinstance(v, (np.floating, np.float64, np.float32, np.float16)):
            if pd.isna(v):
                return None
            return float(v)
        return v
    records = df.to_dict(orient='records')
    for r in records:
        for k, v in list(r.items()):
            r[k] = _cast(v)
    return records

# ======== 메인: 서버 전송 ========
def send_to_server(
        df: pd.DataFrame,
        api_url: str = None,
        token: str = None,
        chunk_size: int = None,
        retries: int = None,
        wait: float = None,
        timeout: int = None,
        column_map: dict = None,
        backup_dir: str = None,
        payload_key: str = "records"  # 서버가 {"records":[...]} 형태를 받을 때
) -> bool:
    """
    학습/예측 결과 DataFrame을 서버로 전송해서 DB에 저장.
    - 청크 단위로 POST 전송
    - 실패 시 재시도, 최종 실패 시 CSV 백업
    """
    if df is None or df.empty:
        print("[send_to_server] 전송할 데이터가 없음")
        return False

    api_url = api_url or API_URL
    token = token or API_TOKEN
    chunk_size = chunk_size or CHUNK_SIZE
    retries = retries if retries is not None else RETRIES
    wait = wait if wait is not None else WAIT
    timeout = timeout or TIMEOUT
    backup_dir = backup_dir or BACKUP_DIR
    os.makedirs(backup_dir, exist_ok=True)

    # 데이터 정리 + 컬럼 매핑
    df_pre = _df_prepare(df)
    if column_map:
        df_pre = _apply_column_map(df_pre, column_map)

    # 세션/헤더 준비
    sess = requests.Session()
    headers = {
        "Content-Type": "application/json; charset=utf-8"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    # 내부 전송 함수
    def _post_records(records: list, attempt: int) -> bool:
        try:
            payload = {payload_key: records}
            # ensure_ascii=False로 한글 그대로 전송
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            resp = sess.post(api_url, data=data, headers=headers, timeout=timeout)
            if 200 <= resp.status_code < 300:
                return True
            print(f"[send_to_server] 실패 응답코드: {resp.status_code} body={resp.text[:200]}")
            return False
        except Exception as e:
            print(f"[send_to_server] 예외 발생({attempt}회): {type(e).__name__}: {e}")
            traceback.print_exc(limit=1)
            return False

    # 청크 전송
    n = len(df_pre)
    parts = 1 if chunk_size is None else math.ceil(n / chunk_size)
    for i in range(parts):
        sub = df_pre.iloc[i * chunk_size : (i + 1) * chunk_size] if parts > 1 else df_pre
        recs = _to_records(sub)

        ok = False
        for attempt in range(1, retries + 1):
            print(f"[send_to_server] 청크 {i+1}/{parts}, 행수={len(recs)}, 시도={attempt}")
            ok = _post_records(recs, attempt)
            if ok:
                break
            time.sleep(wait * attempt)  # 지수 백오프

        if not ok:
            # 실패 청크 백업
            ts = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = f"send_backup_chunk{i+1}_of_{parts}_{ts}.csv"
            path = os.path.join(backup_dir, fname)
            sub.to_csv(path, index=False, encoding="utf-8-sig")
            print(f"[send_to_server] 청크 전송 실패, 백업 저장: {path}")
            return False

    print("[send_to_server] 전체 전송 성공")
    return True

# ======== 사용 예시 ========
if __name__ == "__main__":
    # 예시 out DataFrame 가정
    # out = ...  # 네 파이프라인에서 생성된 결과 DF

    # 보내기
    # 성공 여부에 따라 분기 처리하고 싶으면 아래처럼 사용
    # ok = send_to_server(out, column_map=COLUMN_MAP)
    # if not ok:
    #     print("전송 실패 처리 로직 수행")
    pass
