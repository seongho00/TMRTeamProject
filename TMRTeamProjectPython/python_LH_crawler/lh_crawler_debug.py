# lh_crawler_debug.py  ───────────────────────────
from playwright.sync_api import sync_playwright

URL = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1069"

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,          # 창을 띄워서 확인
        slow_mo=200,             # 동작 0.2초 딜레이
        args=["--no-sandbox"]
    )
    page = browser.new_page()
    page.goto(URL)
    page.pause()                 # ▶ Inspector 열림, F12 로 확인
