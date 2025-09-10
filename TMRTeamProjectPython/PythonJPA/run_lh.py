from datetime import date, datetime
import json, urllib.request
from typing import Dict, Any, List

API_URL = "http://localhost:8080/usr/api/ingest"
API_TIMEOUT = 30
API_KEY = "SECRET_KEY_123"

_bulk_buffer: List[Dict[str, Any]] = []

def _to_json(o):
    if isinstance(o, (date, datetime)):
        return o.isoformat() # "2025-09-22T10:00:00"
    return str(o)

def send_to_java_bulk(payload_list: List[Dict[str, Any]]) -> None:
    data = json.dumps(payload_list, default=_to_json, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
    }
    if API_KEY:
        headers["X-INGEST-KEY"] = API_KEY

    req = urllib.request.Request(API_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            print(f"[INGEST] {resp.status} {body}")
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="ignore")
        print(f"[INGEST-HTTPERROR] {e.code} {err}")
        raise
    except urllib.error.URLError as e:
        print(f"[INGEST-URLERROR] {e}")
        raise

def save_schedule(meta: Dict[str, Any], parsed: Dict[str, Any]) -> None:
    _bulk_buffer.append({
        "listNo": meta.get("list_no"),
        "postType": meta.get("post_type"),
        "name": meta.get("name"),
        "region": meta.get("region"),
        "hasAttach": bool(meta.get("has_attach")),
        "postedDate": meta.get("posted_date"),
        "dueDate": meta.get("due_date"),
        "status": meta.get("status"),
        "applyStart": parsed.get("apply_start"),
        "applyEnd": parsed.get("apply_end"),
        "resultTime": parsed.get("result_time"),
        "contractStart": parsed.get("contract_start"),
        "contractEnd": parsed.get("contract_end"),
        "detailUrl": meta.get("detail_url")
    })

def flush_bulk() -> None:
    if _bulk_buffer:
        send_to_java_bulk(_bulk_buffer)
        _bulk_buffer.clear()

if __name__ == "__main__":
    # 실행기(런처) 모드: 크롤러를 호출
    from crawling.lh_data_crawling import crawl   # 모듈 경로는 실제 폴더명 기준
    print("[PY] launcher: running crawler...")
    crawl()   # 내부에서 save_schedule/flush_bulk 호출됨
    print("[PY] launcher: done.")
