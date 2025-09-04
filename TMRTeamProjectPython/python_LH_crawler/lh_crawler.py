from __future__ import annotations

import re
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from playwright.sync_api import (
    sync_playwright,
    TimeoutError as PlaywrightTimeout,
    Page,
)

# --- 설정값 ---
URL: str = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1069"
TABLE_ROW: str = "table > tbody > tr"
TABLE_HEADER: str = "table > thead > tr"
NEXT_CANDIDATES: List[str] = [
    "a.paging_next:not(.disabled)",
    "button.next:not([disabled])",
    "a[title='다음']",
]
# 상세 페이지에서 공고문 파일이 있는 항목
ATTACHMENT_ITEM_SELECTOR = "div.bbsV_atchmnfl dl.col_red li"

# 유틸 함수
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

# 메인 크롤링
def crawl() -> List[Dict[str, Any]]:
    rows_out: List[Dict[str, Any]] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print("[INFO] open →", URL)
        page.goto(URL, timeout=60_000)

        try:
            agree_button_selector = "div.pop_layer_wrap button.btn_pop_agree"
            page.wait_for_selector(agree_button_selector, timeout=5000)
            print("[INFO] Consent pop-up detected. Clicking 'Agree'.")
            page.click(agree_button_selector)
            page.wait_for_selector(agree_button_selector, state='detached', timeout=5000)
        except PlaywrightTimeout:
            print("[INFO] No consent pop-up detected or already handled.")

        try:
            print("[INFO] Waiting for table to be ready...")
            # networkidle 대신 selector를 기다립니다.
            page.wait_for_selector(TABLE_HEADER, timeout=20_000)
            print("[INFO] Table is ready.")
        except PlaywrightTimeout as e:
            print(f"[ERROR] Page loading failed or table not found: {e}")
            browser.close()
            return rows_out

        page_no = 1

        while True:
            print(f"[INFO] page {page_no}")

            rows_on_page = page.query_selector_all(TABLE_ROW)
            num_rows = len(rows_on_page)

            for i in range(num_rows):
                current_row = page.query_selector_all(TABLE_ROW)[i]

                tds = [td.inner_text().strip() for td in current_row.query_selector_all("td")]
                if len(tds) < 9: continue

                site_no = to_int(tds[0])
                print(f"  > Processing [{site_no}] {tds[2][:20]}...")

                attachments = []
                detail_link = current_row.query_selector("a.wrtancInfoBtn")
                if detail_link:
                    detail_link.click()
                    # networkidle 대신 selector를 기다립니다.
                    page.wait_for_selector(ATTACHMENT_ITEM_SELECTOR, timeout=20_000)

                    attachment_items = page.query_selector_all(ATTACHMENT_ITEM_SELECTOR)
                    for item in attachment_items:
                        file_link = item.query_selector("a:first-child")
                        if file_link:
                            file_name = file_link.inner_text()
                            href = file_link.get_attribute("href")
                            match = re.search(r"fileDownLoad\('(\d+)'\)", href)
                            if match:
                                file_id = match.group(1)
                                download_url = f"https://apply.lh.or.kr/lhapply/lhFile.do?fileid={file_id}"
                                attachments.append({"name": file_name, "url": download_url})

                    page.go_back()
                    # networkidle 대신 selector를 기다립니다.
                    page.wait_for_selector(TABLE_ROW, timeout=20_000)

                rows_out.append({
                    "siteNo": site_no, "type": tds[1], "title": tds[2],
                    "address": tds[3], "postDate": to_std_date(tds[5]),
                    "deadlineDate": to_std_date(tds[6]), "status": tds[7] or None,
                    "views": to_int(tds[8]), "callNumber": None,
                    "attachments": attachments
                })

            if not safe_click(page, NEXT_CANDIDATES):
                break

            # 클릭 후 잠시 대기하고 selector를 기다립니다.
            time.sleep(0.5)
            page.wait_for_selector(TABLE_ROW, timeout=20_000)
            page_no += 1

        browser.close()

    print(f"[INFO] 크롤링 완료: {len(rows_out)} rows")
    return rows_out
