from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

import requests
from requests.adapters import Retry, HTTPAdapter

# 1) 패키지 루트(TMRTeamProjectPython)를 sys.path에 추가
BASE_DIR = Path(__file__).resolve().parent.parent  # .../TMRTeamProjectPython
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# 2) python_LH_crawler 패키지화 보장(없으면 __init__.py 생성)
pkg_dir = BASE_DIR / "python_LH_crawler"
init_py = pkg_dir / "__init__.py"
try:
    if pkg_dir.is_dir() and not init_py.exists():
        init_py.write_text("", encoding="utf-8")
except Exception:
    pass

print(f"[DEBUG] BASE_DIR={BASE_DIR}")
print(f"[DEBUG] sys.path[0]={sys.path[0]}")

# 3) 이제 패키지 임포트
try:
    from python_LH_crawler.lh_crawler import crawl
except Exception as e:
    print(f"[ERROR] import failed: {e}")
    sys.exit(1)

# ===== 전송 설정 =====
SPRING_INGEST_URL = "http://localhost:8080/usr/api/ingest"
SPRING_INGEST_API_KEY = "SECRET_KEY_123"
BATCH_SIZE = 200
TIMEOUT_SEC = 30

def build_session() -> requests.Session:
    s = requests.Session()
    try:
        retries = Retry(
            total=3, read=3, connect=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],  # urllib3 구버전이면 except에서 대체
        )
    except TypeError:
        retries = Retry(
            total=3, read=3, connect=3,
            backoff_factor=0.5,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["POST"],
        )
    s.mount("http://", HTTPAdapter(max_retries=retries))
    s.mount("https://", HTTPAdapter(max_retries=retries))
    return s

def rows_to_ingest_items(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for r in rows:
        items.append({
            "siteNo": r.get("siteNo"),
            "type": r.get("type") or "",
            "title": r.get("title") or "",
            "address": r.get("address") or "",
            "postDate": r.get("postDate"),
            "deadlineDate": r.get("deadlineDate"),
            "status": r.get("status") or "",
            "views": r.get("views"),
            "attachments": r.get("attachments") or [],
        })
    return items

def send_ingest_request(items: List[Dict[str, Any]], batch_size: int = BATCH_SIZE) -> None:
    if not items:
        print("[INFO] 전송할 데이터가 없어요.")
        return

    sess = build_session()
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "X-INGEST-KEY": SPRING_INGEST_API_KEY,
    }

    for i in range(0, len(items), batch_size):
        chunk = items[i:i + batch_size]
        resp = sess.post(
            SPRING_INGEST_URL,
            headers=headers,
            data=json.dumps(chunk, ensure_ascii=False),
            timeout=TIMEOUT_SEC
        )
        print(f"[DEBUG] POST {SPRING_INGEST_URL} → {resp.status_code}")
        if resp.status_code >= 400:
            print(f"[ERROR] ingest failed: {resp.status_code} {resp.text}")
        else:
            print(f"[INFO] ingest ok: {len(chunk)} rows → {resp.text.strip()}")

if __name__ == "__main__":
    try:
        rows = crawl()
        print(f"[INFO] 크롤링 결과: {len(rows)} rows")
    except Exception as e:
        print(f"[ERROR] 크롤러 예외: {e}")
        rows = []

    payload = rows_to_ingest_items(rows)
    send_ingest_request(payload, batch_size=BATCH_SIZE)
