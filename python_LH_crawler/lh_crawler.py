#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
상가 공고 목록 크롤러
---------------------------------
* 매핑 (2025-07-15 기준)
    siteNo       : 1번째 <td> (게시물 번호)
    type         : 2번째 <td> (유형)
    title        : 3번째 <td> (공고명)
    address      : 4번째 <td> (지역)
    postDate     : 6번째 <td> (게시일, yyyy.MM.dd → yyyy-MM-dd)
    deadlineDate : 7번째 <td> (마감일, 〃)
    status       : 8번째 <td> (상태)
    views        : 9번째 <td> (조회수, 콤마 제거 후 int)
    callNumber   : 목록에 표시되지 않음 → None
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeout,
    Page,
)


# 주소
URL: str = (
    "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1069"
)

# 선택자
TABLE_ROW: str = "table > tbody > tr"
TABLE_HEADER: str = "table > thead > tr"
NEXT_CANDIDATES: List[str] = [
    "a.paging_next:not(.disabled)",
    "button.next:not([disabled])",
    "a[title='다음']",
]

# 출력 파일
OUT_FILE: Path = Path(__file__).parent / "data" / "lh_data.json"
OUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# 유틸 (변경 없음)
def to_std_date(txt: str) -> Optional[str]:
    txt = txt.strip()
    if not txt: return None
    try: return datetime.strptime(txt, "%Y.%m.%d").strftime("%Y-%m-%d")
    except ValueError: return None

def to_int(txt: str) -> Optional[int]:
    cleaned = txt.replace(",", "").strip()
    return int(cleaned) if cleaned.isdigit() else None

def safe_click(page: Page, selectors: List[str]) -> bool:
    for sel in selectors:
        try:
            btn = page.query_selector(sel)
            if btn and btn.is_enabled():
                btn.click()
                return True
        except PlaywrightTimeout: pass
    return False

# 메인 크롤링 로직

def crawl() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) # 다시 자동화 모드로 변경
        page = browser.new_page()

        print("[INFO] open →", URL)
        page.goto(URL, timeout=60_000)

        # 팝업 찾아서 클릭
        try:
            # 팝업 버튼 선택
            agree_button_selector = "div.pop_layer_wrap button.btn_pop_agree"

            # 팝업이 나타날 때까지 최대 5초 대기
            page.wait_for_selector(agree_button_selector, timeout=5000)

            print("[INFO] Consent pop-up detected. Clicking 'Agree'.")
            page.click(agree_button_selector)

            # 팝업이 사라질 때까지 대기
            page.wait_for_selector(agree_button_selector, state='detached', timeout=5000)

        except PlaywrightTimeout:
            # 5초 내에 팝업이 안 뜨면 동의했거나 없는 경우이므로 통과
            print("[INFO] No consent pop-up detected or already handled.")

        try:
            print("[INFO] Waiting for table to be ready...")
            page.wait_for_load_state("networkidle", timeout=20_000)
            page.wait_for_selector(TABLE_HEADER, timeout=10_000)
            print("[INFO] Table is ready.")

        except PlaywrightTimeout as e:
            print(f"[ERROR] Page loading failed or table not found: {e}")
            browser.close()
            return

        rows_out: List[Dict[str, Any]] = []
        page_no = 1

        while True:
            print(f"[INFO] page {page_no}")

            for row in page.query_selector_all(TABLE_ROW):
                tds = [td.inner_text().strip() for td in row.query_selector_all("td")]
                if len(tds) < 9:
                    continue

                site_no = to_int(tds[0])
                rows_out.append({
                    "siteNo": site_no, "type": tds[1], "title": tds[2],
                    "address": tds[3], "postDate": to_std_date(tds[5]),
                    "deadlineDate": to_std_date(tds[6]), "status": tds[7] or None,
                    "views": to_int(tds[8]), "callNumber": None,
                })

            if not safe_click(page, NEXT_CANDIDATES):
                break

            page.wait_for_load_state("networkidle", timeout=20_000)
            page_no += 1
            time.sleep(0.5)

        browser.close()

    OUT_FILE.write_text(json.dumps(rows_out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[INFO] saved → {OUT_FILE} ({len(rows_out)} rows)")


# main 함수
if __name__ == "__main__":
    crawl()