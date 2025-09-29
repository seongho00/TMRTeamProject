import time

from playwright.sync_api import sync_playwright
from contextlib import nullcontext
from playwright.sync_api import Page, Locator, TimeoutError as PWTimeout
import re


def wait_for_element(page: Page, selector: str, timeout: int = 6000) -> Locator:
    loc = page.locator(selector)
    loc.wait_for(state="visible", timeout=timeout)
    return loc


def wait_for_elements(page: Page, selector: str, min_count: int = 1, timeout: int = 6000):
    page.wait_for_selector(selector, state="attached", timeout=timeout)
    loc = page.locator(selector)
    # 개수 만족까지 폴링
    with page.expect_event("load", timeout=200) if False else nullcontext():  # no-op
        end = page.context._impl_obj._loop.time() + (timeout / 1000)
        while True:
            if loc.count() >= min_count:
                break
            if page.context._impl_obj._loop.time() > end:
                raise PWTimeout(f"Timeout waiting for {min_count}+ elements: {selector}")
    return [loc.nth(i) for i in range(loc.count())]


def wait_for_child_element(parent: Locator, selector: str, timeout: int = 6000) -> Locator:
    child = parent.locator(selector)
    child.wait_for(state="visible", timeout=timeout)
    return child


USER_DATA_DIR = "./.chrome-profile"  # 크롬 프로필(쿠키/세션) 저장 위치

with sync_playwright() as p:
    # 로컬 크롬 실행 (chromedriver 필요 없음)
    browser = p.chromium.launch_persistent_context(
        user_data_dir=USER_DATA_DIR,
        channel="chrome",  # ⚡ 로컬 설치된 Chrome 사용
        headless=False,  # True로 하면 창 안 뜸
        locale="ko-KR",
        viewport={"width": 1280, "height": 860},
        ignore_https_errors=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-first-run", "--no-default-browser-check",
            "--disable-dev-shm-use", "--no-sandbox",
        ],
    )

    page = browser.new_page()

    # 홈택스 페이지 접속
    page.goto(
        "https://www.realtyprice.kr/notice/gsindividual/search.htm")


    sidoNm ="서울특별시"
    sggNm = "서초구"
    emdNm = "서초동"

    bun = "1317"
    ji = "20"

    # 시도 선택
    sido_select = page.locator("#sido_list")
    sido_select.select_option(label=sidoNm)

    # 시군구 선택
    sgg_select = page.locator("#sgg_list")  # id 선택자는 # 으로
    sgg_select.select_option(label=sggNm)

    # 행정동 선택
    emd_select = page.locator("#eub_list") # id 선택자는 # 으로
    emd_select.select_option(label=emdNm)

    # bun1 입력칸 (본번)
    # 부모 div 기준으로 locator를 좁힘
    container = page.locator("div.search-opt3")

    # bun1 locator 찾기
    bun1_input = container.locator("input[name='bun1']")
    bun2_input = container.locator("input[name='bun2']")
    bun1_input.fill(bun)
    bun2_input.fill(ji)

    # 1) class="search-bt" 안의 버튼 클릭
    page.click(".search-bt input[type='image']")

    # 데이터 가져오기 선택
    # tbody 선택
    # tr이 생길 때까지 기다림
    page.wait_for_selector("#dataList tr", timeout=10000)

    # 첫 번째 tr
    first_row = page.locator("#dataList tr").first
    tds = first_row.locator("td")

    # 토지시가 데이터 (index=3)
    price_text = first_row.locator("td").nth(3).inner_text().strip()

    # 숫자만 추출 (원/㎡ 제거)
    price_value = re.sub(r"[^0-9]", "", price_text)  # "79730000"
    price_value = int(price_value)

    print("숫자 기준시가:", price_value)  # 79730000

    browser.close()
