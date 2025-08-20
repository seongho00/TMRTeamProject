import re
import time
from datetime import datetime

import pymysql
from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# ====== 공통 유틸 ======
def wait_for_elements(driver, by, value, min_count=1, timeout=10):
    # 특정 셀렉터의 요소가 일정 개수 이상 나올 때까지 대기
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(by, value)) >= min_count
    )
    return driver.find_elements(by, value)


def wait_for_child_element(parent_element, by, value, timeout=10):
    # 부모 요소 안에서 자식 요소 1개 대기
    return WebDriverWait(parent_element, timeout).until(
        lambda el: el.find_element(by, value)
    )


def wait_for_child_elements(parent_element, by, value, min_count=1, timeout=10):
    # 부모 요소 안에서 자식 요소 N개 이상 대기
    WebDriverWait(parent_element, timeout).until(
        lambda el: len(el.find_elements(by, value)) >= min_count
    )
    return parent_element.find_elements(by, value)


def dom_ready(driver, timeout=15):
    # DOM 로드 완료 대기
    WebDriverWait(driver, timeout).until(
        lambda d: d.execute_script("return document.readyState") == "complete"
    )


def wait_overlay_gone(driver, selectors=None, timeout=8):
    # 로딩오버레이/모달/쿠키배너 등 클릭 인터셉트 방지용 대기
    if not selectors:
        return
    end = time.time() + timeout
    while time.time() < end:
        try:
            visible = False
            for css in selectors:
                elems = driver.find_elements(By.CSS_SELECTOR, css)
                for e in elems:
                    if e.is_displayed():
                        visible = True
                        break
                if visible:
                    break
            if not visible:
                return
        except StaleElementReferenceException:
            pass
        time.sleep(0.2)


def scroll_to_center(driver, el):
    # 요소를 화면 중앙으로 스크롤(고정 헤더/배너 겹침 최소화)
    driver.execute_script(
        """
        const el = arguments[0];
        const r = el.getBoundingClientRect();
        window.scrollBy({top: r.top - (window.innerHeight/2) + (r.height/2), left: 0, behavior: 'instant'});
        """,
        el,
    )


def safe_click(driver, element=None, locator=None, timeout=10, retries=4, overlays=None):
    # 안전 클릭: clickable 대기 → 기본 클릭 → JS 클릭 → 오프셋 클릭 순서로 재시도
    if element is None and locator is None:
        raise ValueError("element 또는 locator 중 하나는 필수")

    wait = WebDriverWait(driver, timeout)

    # 요소 준비
    if element is None:
        element = wait.until(EC.presence_of_element_located(locator))

    last_err = None
    for attempt in range(1, retries + 1):
        try:
            # 표시/활성 대기
            wait.until(EC.visibility_of(element))

            # 오버레이 사라질 때까지
            wait_overlay_gone(driver, overlays, timeout=5)

            # 화면 중앙으로 이동
            scroll_to_center(driver, element)
            time.sleep(0.05)

            # clickable 대기 (locator가 있으면 그것으로, 없으면 JS로 포커스 유도)
            try:
                if locator:
                    wait.until(EC.element_to_be_clickable(locator))
            except Exception:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
                except Exception:
                    pass

            # 1) 기본 클릭
            element.click()
            return True

        except ElementClickInterceptedException as e:
            last_err = e

            # 2) JS 클릭 시도
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                pass

            # 3) 오프셋 클릭(ActionChains)
            try:
                ActionChains(driver).move_to_element_with_offset(element, 0, 10).click().perform()
                return True
            except Exception:
                pass

            # 살짝 스크롤 보정 후 재시도
            driver.execute_script("window.scrollBy(0, -80);")
            time.sleep(0.2)

            # DOM 갱신 대비 재조회
            if locator:
                try:
                    element = wait.until(EC.presence_of_element_located(locator))
                except TimeoutException as te:
                    last_err = te

        except StaleElementReferenceException as e:
            last_err = e
            if locator:
                element = wait.until(EC.presence_of_element_located(locator))
            else:
                raise

    if last_err:
        raise last_err
    return False


def switch_iframe_until_sub_container(driver, timeout=10):
    # 기본 → 모든 iframe 순회하며 #sub_container 존재하는 컨텍스트 찾기
    # 찾으면 True, 아니면 False
    try:
        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "sub_container")))
        return True
    except TimeoutException:
        pass

    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    for f in iframes:
        driver.switch_to.default_content()
        driver.switch_to.frame(f)
        try:
            WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.ID, "sub_container")))
            return True
        except TimeoutException:
            continue
    driver.switch_to.default_content()
    return False


# ====== LH '공급일정' 추출 로직 ======
def find_supply_schedule(driver, idx, timeout=10, attempts=3):
    """
    상세 페이지에서 '공급일정' li/table을 찾아 text 리스트로 반환.
    실패하면 (None, reason) 반환.
    """
    last_reason = ""
    for attempt in range(1, attempts + 1):
        try:
            dom_ready(driver, timeout=timeout)

            # NetFunnel/로딩 레이어가 있다면 사라질 때까지 (있으면)
            try:
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script("""
                        const el = document.querySelector('#NetFunnel_Skin, .NetFunnel_Loading_Pannel, #loading');
                        if(!el) return true;
                        const s = getComputedStyle(el);
                        return s.display === 'none' || el.style.display === 'none';
                    """)
                )
            except TimeoutException:
                pass

            ok = switch_iframe_until_sub_container(driver, timeout=timeout)
            if not ok:
                last_reason = "no #sub_container"
                raise TimeoutException(last_reason)

            # 공급일정 h3 탐색
            try:
                h3_elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#sub_container h3.tit1"))
                )
            except TimeoutException:
                last_reason = "no h3.tit1"
                raise

            target_h3 = None
            for h in h3_elements:
                if "공급일정" in (h.text or ""):
                    target_h3 = h
                    break

            if not target_h3:
                try:
                    target_h3 = driver.find_element(
                        By.XPATH,
                        "//*[@id='sub_container']//h3[contains(@class,'tit1')][contains(normalize-space(.),'공급일정')]"
                    )
                except NoSuchElementException:
                    last_reason = "no '공급일정' heading"
                    raise TimeoutException(last_reason)

            items = extract_items(target_h3)
            if items:
                return items, None

            last_reason = "no schedule items (li/table)"
            raise TimeoutException(last_reason)

        except (TimeoutException, StaleElementReferenceException) as e:
            if attempt < attempts:
                print(f"   [재시도 {attempt}/{attempts}] idx={idx + 1}, reason={last_reason or type(e).__name__}")
                driver.switch_to.default_content()
                time.sleep(0.4)
                continue
            else:
                driver.switch_to.default_content()
                return None, (last_reason or type(e).__name__)

    return None, (last_reason or "unknown")


def extract_items(target_h3):
    """
    return {"type": "table"|"li", "table_lines": [str...], "li_lines": [str...]}
    """
    table_lines = []
    tables = target_h3.find_elements(By.XPATH, "following-sibling::*[not(self::h3)]//table")
    for table in tables:
        for row in table.find_elements(By.XPATH, ".//tbody/tr"):
            tds = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
            tds = [t for t in tds if t]
            if tds:
                table_lines.append(" | ".join(tds))

    lis = target_h3.find_elements(By.XPATH, "following-sibling::*//li")
    li_lines = [li.text.strip() for li in lis if li.text.strip()]

    if table_lines:
        return {"type": "table", "table_lines": table_lines, "li_lines": li_lines}
    return {"type": "li", "table_lines": [], "li_lines": li_lines}


DT = "%Y.%m.%d %H:%M"
D = "%Y.%m.%d"


def _clean(s: str) -> str:
    s = s.replace("\u00A0", " ").replace("\u200B", "")
    s = s.replace("∼", "~").replace("〜", "~").replace("－", "-")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\(([^)]*)\)", r"\1", s)
    return s.strip()


def _dt(s: str) -> datetime:
    s = _clean(s)
    if re.search(r"\d{1,2}:\d{2}", s):
        return datetime.strptime(s, DT)
    return datetime.strptime(s, D)


def parse_table_lines(lines):
    parsed = {
        "rows": [],
        "contract_start": None,
        "contract_end": None,
    }

    for raw in lines:
        line = raw.strip()
        if not line or "입찰일정" in line:
            continue

        if line.replace(" ", "").startswith("계약체결일정:"):
            m = re.search(r"계약체결일정\s*:\s*(\d{4}\.\d{1,2}\.\d{1,2})\s*[~\-]\s*(\d{4}\.\d{1,2}\.\d{1,2})", _clean(line))
            if m:
                parsed["contract_start"] = _dt(m.group(1)).date()
                parsed["contract_end"] = _dt(m.group(2)).date()
            continue

        if "|" not in line:
            continue

        parts = [p.strip() for p in line.split("|")]
        label = parts[0] if parts else ""

        apply_start = apply_end = None
        if len(parts) >= 2:
            col2 = _clean(parts[1])
            d_match = re.search(r"\d{4}\.\d{1,2}\.\d{1,2}", col2)
            times = re.findall(r"\d{1,2}:\d{2}", col2)
            if d_match and len(times) >= 2:
                d = d_match.group()
                t1, t2 = times[0], times[1]
                apply_start = _dt(f"{d} {t1}")
                apply_end = _dt(f"{d} {t2}")

        def extract_dt_from_col(col_text: str):
            col = _clean(col_text)
            d2 = re.search(r"\d{4}\.\d{1,2}\.\d{1,2}", col)
            if not d2:
                return None
            t2 = re.search(r"\d{1,2}:\d{2}", col)
            return _dt(f"{d2.group()} {t2.group() if t2 else '00:00'}")

        result_time = None
        if len(parts) >= 2:
            result_time = extract_dt_from_col(parts[-1])
        if result_time is None and len(parts) >= 3:
            result_time = extract_dt_from_col(parts[-2])

        parsed["rows"].append({
            "label": label,
            "apply_start": apply_start,
            "apply_end": apply_end,
            "result_time": result_time
        })

    return parsed


def choose_primary(parsed_table):
    rows = [r for r in parsed_table["rows"] if r["apply_start"] and r["apply_end"]]
    result = {"apply_start": None, "apply_end": None, "result_time": None,
              "contract_start": parsed_table["contract_start"], "contract_end": parsed_table["contract_end"]}

    chosen = None
    if rows:
        firsts = [r for r in rows if str(r["label"]).startswith("최초")]
        chosen = firsts[0] if firsts else sorted(rows, key=lambda x: x["apply_start"])[0]
        result["apply_start"] = chosen["apply_start"]
        result["apply_end"] = chosen["apply_end"]

    rts = [r for r in parsed_table["rows"] if r["result_time"]]
    if rts:
        if chosen:
            same = [r for r in rts if r["label"] == chosen["label"]]
            result["result_time"] = (same[0]["result_time"] if same
                                     else sorted(rts, key=lambda x: x["result_time"])[0]["result_time"])
        else:
            result["result_time"] = sorted(rts, key=lambda x: x["result_time"])[0]["result_time"]

    return result


def parse_li_texts(texts):
    data = {"apply_start": None, "apply_end": None, "result_time": None, "contract_start": None, "contract_end": None}

    for raw in texts:
        txt = _clean(raw)

        m = re.search(
            r"^신청일시\s*:\s*(\d{4}\.\d{1,2}\.\d{1,2})\s*(\d{1,2}:\d{2})\s*[~\-]\s*(?:(\d{4}\.\d{1,2}\.\d{1,2})\s*)?(\d{1,2}:\d{2})",
            txt
        )
        if m:
            d1, t1, d2_opt, t2 = m.groups()
            d2 = d2_opt or d1
            data["apply_start"] = _dt(f"{d1} {t1}")
            data["apply_end"] = _dt(f"{d2} {t2}")
            continue

        m = re.search(
            r"^(?:결과발표일시|개찰결과게시일시)\s*:\s*(\d{4}\.\d{1,2}\.\d{1,2})(?:\s*(\d{1,2}:\d{2}))?",
            txt
        )
        if m:
            d, t = m.groups()
            data["result_time"] = _dt(f"{d} {t or '00:00'}")
            continue

        m = re.search(
            r"^계약체결일정\s*:\s*(\d{4}\.\d{1,2}\.\d{1,2})\s*[~\-]\s*(\d{4}\.\d{1,2}\.\d{1,2})",
            txt
        )
        if m:
            data["contract_start"] = _dt(m.group(1)).date()
            data["contract_end"] = _dt(m.group(2)).date()
            continue

    return data


# ====== DB 연결 ======
conn = pymysql.connect(
    host="localhost",
    user="root",
    password="1234",
    database="TMRTeamProject",
    charset="utf8mb4"
)
cursor = conn.cursor()

UPSERT_SQL = """
             INSERT INTO lh_supply_schedule
             (name, apply_start, apply_end, result_time, contract_start, contract_end)
             VALUES (%s, %s, %s, %s, %s, %s)
                 ON DUPLICATE KEY UPDATE
                                      apply_end=VALUES(apply_end),
                                      result_time=VALUES(result_time),
                                      contract_start=VALUES(contract_start),
                                      contract_end=VALUES(contract_end),
                                      update_date=CURRENT_TIMESTAMP \
             """


def save_schedule(name, parsed):
    cursor.execute(UPSERT_SQL, (
        name,
        parsed.get("apply_start"),
        parsed.get("apply_end"),
        parsed.get("result_time"),
        parsed.get("contract_start"),
        parsed.get("contract_end"),
    ))
    conn.commit()


# ====== 크롬 옵션/드라이버 ======
chrome_options = Options()
chrome_options.add_argument("--headless=new")     # 최신 헤드리스
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(service=Service("chromedriver.exe"), options=chrome_options)

# 오버레이 후보 셀렉터 (사이트 상황에 맞게 추가/수정 가능)
OVERLAYS = [".loading", ".spinner", ".modal-backdrop", "#overlay", ".cookie-banner", "#NetFunnel_Skin", ".NetFunnel_Loading_Pannel", "#loading"]

# ====== 크롤링 시작 ======
driver.get("https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1069")
dom_ready(driver, timeout=20)
wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=20)

missing_supply_schedule = []

while True:
    rows = wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=15)

    for idx in range(len(rows)):
        # 매 사이클마다 fresh 조회 (stale 방지)
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        link = rows[idx].find_element(By.CSS_SELECTOR, "a")
        span = link.find_element(By.CSS_SELECTOR, "span")
        name = span.text.strip()

        print(f"{idx + 1}번째 공고 이름: {name}")

        old_url = driver.current_url

        # 안전 클릭으로 상세 진입
        safe_click(driver, element=link, overlays=OVERLAYS, retries=4, timeout=12)

        # URL 변경 또는 상세의 대표 요소 대기
        try:
            WebDriverWait(driver, 12).until(lambda d: d.current_url != old_url)
        except TimeoutException:
            # 일부 케이스는 동적 컨텐츠만 바뀔 수 있으므로 대표 요소로도 보조 대기
            WebDriverWait(driver, 12).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "table, .view, .detail, #sub_container"))
            )

        # 공급일정 추출
        texts, reason = find_supply_schedule(driver, idx, timeout=12, attempts=3)
        if not texts:
            print(f"⚠ {idx + 1}번째 공고 - 공급일정 추출 실패: {reason}")
            missing_supply_schedule.append((idx + 1, reason))
        else:
            # 파싱/저장
            if texts["type"] == "table":
                tparsed = parse_table_lines(texts["table_lines"])
                parsed = choose_primary(tparsed)

                if (parsed.get("contract_start") is None or parsed.get("contract_end") is None) and texts["li_lines"]:
                    li_fix = parse_li_texts(texts["li_lines"])
                    if parsed.get("contract_start") is None and li_fix.get("contract_start"):
                        parsed["contract_start"] = li_fix["contract_start"]
                    if parsed.get("contract_end") is None and li_fix.get("contract_end"):
                        parsed["contract_end"] = li_fix["contract_end"]

                save_schedule(name, parsed)
                print("DB saved (table):", name, parsed)

            elif texts["type"] == "li":
                parsed = parse_li_texts(texts["li_lines"])
                save_schedule(name, parsed)
                print("DB saved (li):", name, parsed)

        # 뒤로 가기 안정화
        try:
            driver.execute_script("window.history.back();")
        except Exception:
            driver.back()

        # 목록 재로딩 대기
        dom_ready(driver, timeout=15)
        wait_overlay_gone(driver, OVERLAYS, timeout=6)
        wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=15)
        print("-----------------------------")
        time.sleep(0.4)

    # 페이지네이션: 다음 버튼 안전 클릭
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.page_next")
        # disabled 클래스 판단
        cls = next_btn.get_attribute("class") or ""
        if "disabled" in cls.lower():
            print("📌 마지막 페이지 도달")
            break

        old_url = driver.current_url
        safe_click(driver, element=next_btn, overlays=OVERLAYS, retries=3, timeout=10)

        # 페이지 전환 대기
        try:
            WebDriverWait(driver, 10).until(lambda d: d.current_url != old_url)
        except TimeoutException:
            pass

        dom_ready(driver, timeout=15)
        wait_overlay_gone(driver, OVERLAYS, timeout=6)
        wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=15)

    except NoSuchElementException:
        print("📌 다음 버튼 없음, 종료")
        break

# 정리
cursor.close()
conn.close()
driver.quit()
