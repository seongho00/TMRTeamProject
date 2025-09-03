import time

from playwright.sync_api import sync_playwright
from contextlib import nullcontext
from playwright.sync_api import Page, Locator, TimeoutError as PWTimeout

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
        "https://hometax.go.kr/websquare/websquare.html?w2xPath=/ui/pp/index_pp.xml&tmIdx=47&tm2lIdx=4712090000&tm3lIdx=4712090300")

    # 법정동 버튼 대기 후 클릭
    btn = wait_for_element(page, "#mf_txppWframe_btnLdCdPop")  # id 선택자는 # 으로
    btn.click()

    time.sleep(0.5)
    # 행정동 input 찾기
    emd_input_box = wait_for_element(page, "#mf_txppWframe_UTECMAAA08_wframe_inputSchNm")

    # 값 입력
    emd_input_box.fill("서초동")


    # 조회하기 버튼 대기 후 클릭
    btn = wait_for_element(page, "#mf_txppWframe_UTECMAAA08_wframe_trigger6")  # id 선택자는 # 으로
    btn.click()

    time.sleep(1)

    # tbody 선택
    tbody = wait_for_element(page, "#mf_txppWframe_UTECMAAA08_wframe_ldCdAdmDVOList_body_tbody")

    # tr 전부 가져오기
    rows = tbody.locator("tr")

    # tr 개수 확인
    row_count = rows.count()
    print("행 개수:", row_count)
    
    target_sido = "서울특별시"
    target_sgg = "서초구"

    for i in range(row_count):
        row = rows.nth(i)
        cols = row.locator("td")

        # 첫 번째, 두 번째 칼럼 텍스트만 추출
        first_col = cols.nth(0).inner_text().strip()
        second_col = cols.nth(1).inner_text().strip()

        print(first_col, second_col)

        # 원하는 지역 비교
        if target_sido in first_col and target_sgg in second_col:
            print("✅ 찾음:", first_col, second_col)
            # 필요하면 여기서 row.click() 같은 동작도 가능
            btn = cols.nth(6).locator("button")   # td 안에 버튼 요소
            btn.click()

            break




# 예시: 도로명 입력 (실제 셀렉터는 F12로 확인 필요)
    page.wait_for_selector("#textbox-도로명입력아이디", timeout=20000).fill("강남대로")

    # 조회 버튼 클릭 (실제 CSS 셀렉터 확인 필요)
    page.click("button.조회버튼-CSS")

    # 결과 테이블 대기
    table = page.wait_for_selector("table.resultTable", timeout=20000)

    # 테이블 데이터 출력
    rows = table.query_selector_all("tr")
    for row in rows:
        cols = row.query_selector_all("td")
        print([col.inner_text().strip() for col in cols])

    browser.close()
