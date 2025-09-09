import re
import time
from datetime import datetime
from urllib.parse import urlencode, urlparse, parse_qs

from selenium import webdriver
from selenium.common.exceptions import (
    TimeoutException,
    StaleElementReferenceException,
    NoSuchElementException,
    ElementClickInterceptedException,
)
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from PythonJPA.run_lh import save_schedule, flush_bulk

# 설정
LIST_URL = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1069"
DETAIL_BASE = "https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancInfo.do"
PAGE_WAIT = 15  # 페이지 로딩 대기 기본값


# 공통 유틸
def wait_for_elements(driver, by, value, min_count=1, timeout=10):
    WebDriverWait(driver, timeout).until(lambda d: len(d.find_elements(by, value)) >= min_count)
    return driver.find_elements(by, value)


def dom_ready(driver, timeout=15):
    WebDriverWait(driver, timeout).until(lambda d: d.execute_script("return document.readyState") == "complete")


def wait_overlay_gone(driver, selectors=None, timeout=8):
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
    driver.execute_script(
        """
        const el = arguments[0];
        const r = el.getBoundingClientRect();
        window.scrollBy({top: r.top - (window.innerHeight/2) + (r.height/2), left: 0, behavior: 'instant'});
        """,
        el,
    )


def safe_click(driver, element=None, locator=None, timeout=10, retries=4, overlays=None):
    if element is None and locator is None:
        raise ValueError("element 또는 locator 중 하나는 필수")

    wait = WebDriverWait(driver, timeout)
    if element is None:
        element = wait.until(EC.presence_of_element_located(locator))

    last_err = None
    for _ in range(retries):
        try:
            wait.until(EC.visibility_of(element))
            wait_overlay_gone(driver, overlays, timeout=5)
            scroll_to_center(driver, element)
            time.sleep(0.05)
            try:
                if locator:
                    wait.until(EC.element_to_be_clickable(locator))
            except Exception:
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", element)
                except Exception:
                    pass
            element.click()
            return True
        except ElementClickInterceptedException as e:
            last_err = e
            try:
                driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                pass
            try:
                ActionChains(driver).move_to_element_with_offset(element, 0, 10).click().perform()
                return True
            except Exception:
                pass
            driver.execute_script("window.scrollBy(0, -80);")
            time.sleep(0.2)
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


def switch_iframe_until_sub_container(driver):
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


# 리스트 메타 파싱
def _clean(s: str) -> str:
    s = s.replace("\u00A0", " ").replace("\u200B", "")
    s = s.replace("∼", "~").replace("〜", "~").replace("－", "-")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\(([^)]*)\)", r"\1", s)
    return s.strip()


D = "%Y.%m.%d"
DT = "%Y.%m.%d %H:%M"


def _d_or_none(s: str):
    s = _clean(s)
    m = re.search(r"\d{4}\.\d{1,2}\.\d{1,2}", s)
    if not m:
        return None
    return datetime.strptime(m.group(), D).date()


def extract_site_no_from_link(link_el):
    href = link_el.get_attribute("href") or ""
    if "siteNo=" in href:
        qs = parse_qs(urlparse(href).query)
        v = qs.get("siteNo", [None])[0]
        return int(v) if v and v.isdigit() else None
    onclick = link_el.get_attribute("onclick") or ""
    m = re.search(r"siteNo\s*[:=]\s*['\"]?(\d+)['\"]?", onclick)
    if m:
        return int(m.group(1))
    m2 = re.search(r"\((\d{4,})\)", onclick)
    return int(m2.group(1)) if m2 else None


def parse_list_row(row):
    tds = row.find_elements(By.CSS_SELECTOR, "td")

    def _get(i):
        return (tds[i].text or "").strip() if len(tds) > i else ""

    list_no_txt = _get(0)
    post_type = _get(1)

    name = ""
    link_el = None
    try:
        link_el = tds[2].find_element(By.CSS_SELECTOR, "a")
        try:
            name = link_el.find_element(By.CSS_SELECTOR, "span").text.strip()
        except Exception:
            name = link_el.text.strip()
    except Exception:
        name = _get(2)

    region = _get(3)
    has_attach = 1 if (len(tds) > 4 and tds[4].find_elements(By.CSS_SELECTOR, "a, img, i, svg")) else 0
    posted_date = _d_or_none(_get(5))
    due_date = _d_or_none(_get(6))
    status = _get(7)
    site_no = extract_site_no_from_link(link_el) if link_el else None

    try:
        list_no = int(re.sub(r"[^\d]", "", list_no_txt)) if list_no_txt else None
    except Exception:
        list_no = None

    return {
        "list_no": list_no,             # 번호
        "post_type": post_type,         # 유형
        "name": name,                   # 공고명
        "region": region,               # 지역
        "has_attach": has_attach,       # 첨부파일 유무
        "posted_date": posted_date,     # 게시일
        "due_date": due_date,           # 마감일
        "status": status,               # 상태
        "site_no": site_no,             # 상세페이지 고유 식별자
        "link_el": link_el,             # link 추출용
    }


# 상세 이동
def build_detail_url(site_no: int, mi: int = 1069) -> str:
    return f"{DETAIL_BASE}?{urlencode({'mi': mi, 'siteNo': site_no})}"


def goto_detail_by_site_no(driver, site_no: int, mi: int = 1069):
    url = build_detail_url(site_no, mi)
    driver.get(url)
    dom_ready(driver, timeout=PAGE_WAIT)


# 공급일정 섹션 찾기/파싱
def _dt(s: str) -> datetime:
    s = _clean(s)
    if re.search(r"\d{1,2}:\d{2}", s):
        return datetime.strptime(s, DT)
    return datetime.strptime(s, D)


def find_supply_schedule(driver, idx, timeout=10, attempts=3):
    last_reason = ""
    for attempt in range(1, attempts + 1):
        try:
            dom_ready(driver, timeout=timeout)

            try:
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script(
                        """
                        const el = document.querySelector('#NetFunnel_Skin, .NetFunnel_Loading_Pannel, #loading');
                        if(!el) return true;
                        const s = getComputedStyle(el);
                        return s.display === 'none' || el.style.display === 'none';
                        """
                    )
                )
            except TimeoutException:
                pass

            ok = switch_iframe_until_sub_container(driver)
            if not ok:
                last_reason = "no #sub_container"
                raise TimeoutException(last_reason)

            _activate_schedule_section(driver)

            target_h = _find_schedule_heading(driver)
            if not target_h:
                last_reason = "no schedule heading"
                raise TimeoutException(last_reason)

            items = extract_items(target_h)
            if items and (items.get("table_lines") or items.get("li_lines")):
                return items, None

            items = _extract_items_fallback(target_h)
            if items and (items.get("table_lines") or items.get("li_lines")):
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


def _activate_schedule_section(driver):
    candidates = ["공급일정", "모집일정", "신청일정", "공고일정", "일정"]
    for txt in candidates:
        btns = driver.find_elements(
            By.XPATH,
            f"//*[@id='sub_container']//*[self::a or self::button or self::li or self::div][contains(normalize-space(.), '{txt}')]"
        )
        for b in btns:
            try:
                selected = (b.get_attribute("aria-selected") or "").lower() == "true"
                expanded = (b.get_attribute("aria-expanded") or "").lower() == "true"
                cls = (b.get_attribute("class") or "").lower()
                if selected or expanded or "active" in cls:
                    return
                scroll_to_center(driver, b)
                driver.execute_script("arguments[0].click();", b)
                time.sleep(0.15)
                return
            except Exception:
                pass
    accs = driver.find_elements(
        By.XPATH,
        "//*[@id='sub_container']//*[@aria-controls or @data-target or contains(@class,'accordion') or contains(@class,'collapse')]"
    )
    for a in accs:
        try:
            expanded = (a.get_attribute("aria-expanded") or "").lower()
            if expanded in ("false", ""):
                scroll_to_center(driver, a)
                driver.execute_script("arguments[0].click();", a)
                time.sleep(0.15)
        except Exception:
            continue


def _find_schedule_heading(driver):
    try:
        h3s = WebDriverWait(driver, 4).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#sub_container h3.tit1")))
        for h in h3s:
            if any(k in (h.text or "") for k in ["공급일정", "모집일정", "신청일정", "공고일정"]):
                return h
    except TimeoutException:
        pass
    for tag in ["h2", "h3", "h4", "h5"]:
        hs = driver.find_elements(By.CSS_SELECTOR, f"#sub_container {tag}")
        for h in hs:
            t = (h.text or "").strip()
            if any(k in t for k in ["공급일정", "모집일정", "신청일정", "공고일정", "일정"]):
                return h
    labels = driver.find_elements(By.CSS_SELECTOR, "#sub_container legend, #sub_container strong, #sub_container .tit1, #sub_container .title")
    for l in labels:
        t = (l.text or "").strip()
        if any(k in t for k in ["공급일정", "모집일정", "신청일정", "공고일정", "일정"]):
            return l
    return None


def extract_items(target_h3):
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


def _extract_items_fallback(target_root):
    table_lines = []
    li_lines = []

    dls = target_root.find_elements(By.XPATH, "following-sibling::*[not(self::h1 or self::h2 or self::h3)]//dl")
    for dl in dls:
        dts = dl.find_elements(By.TAG_NAME, "dt")
        dds = dl.find_elements(By.TAG_NAME, "dd")
        for i in range(max(len(dts), len(dds))):
            dt = (dts[i].text.strip() if i < len(dts) else "").replace("\n", " ")
            dd = (dds[i].text.strip() if i < len(dds) else "").replace("\n", " ")
            if dt or dd:
                table_lines.append(" | ".join([p for p in [dt, dd] if p]))

    rows = target_root.find_elements(
        By.XPATH,
        "following-sibling::*[not(self::h1 or self::h2 or self::h3)]//*[contains(@class,'row') or contains(@class,'item') or contains(@class,'desc')]"
    )
    for r in rows:
        try:
            lab = r.find_element(By.XPATH, ".//*[self::strong or self::*[contains(@class,'label')]]").text.strip()
            val = r.find_element(By.XPATH, ".//*[self::span or self::p or self::*[contains(@class,'value')]]").text.strip()
            if lab or val:
                table_lines.append(" | ".join([p for p in [lab, val] if p]))
        except Exception:
            continue

    lis = target_root.find_elements(By.XPATH, "following-sibling::*[not(self::h1 or self::h2 or self::h3)]//li")
    for li in lis:
        t = li.text.strip()
        if t:
            li_lines.append(t)

    if table_lines or li_lines:
        return {"type": "table" if table_lines else "li", "table_lines": table_lines, "li_lines": li_lines}
    return {"type": "li", "table_lines": [], "li_lines": []}


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
    result = {
        "apply_start": None,
        "apply_end": None,
        "result_time": None,
        "contract_start": parsed_table["contract_start"],
        "contract_end": parsed_table["contract_end"],
    }

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


# 실행
def crawl():
    # 크롬 옵션 설정
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    # 드라이버 생성
    driver = webdriver.Chrome(options=chrome_options)

    # 오버레이 셀렉터 후보
    OVERLAYS = [
        ".loading", ".spinner", ".modal-backdrop", "#overlay", ".cookie-banner",
        "#NetFunnel_Skin", ".NetFunnel_Loading_Pannel", "#loading"
    ]

    try:
        # 목록 진입 및 초기 로딩 대기
        driver.get(LIST_URL)
        dom_ready(driver, timeout=PAGE_WAIT)
        wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=PAGE_WAIT)

        missing_supply_schedule = []

        while True:
            # 현재 페이지의 행 스냅샷 확보
            rows = wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=15)

            for idx, _ in enumerate(rows, start=1):
                # 매 루프마다 fresh 조회(stale 방지)
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                row = rows[idx - 1]

                # 목록 메타 파싱
                meta = parse_list_row(row)
                print(f"{idx}번째: {meta.get('name')} / 상태:{meta.get('status')} / listNo:{meta.get('list_no')}")

                # 상세 페이지로 이동
                if meta.get("site_no"):
                    # siteNo로 바로 상세 URL 접근
                    goto_detail_by_site_no(driver, meta["site_no"])
                else:
                    # 링크 요소가 있으면 안전 클릭, 없으면 일정 None으로 저장 후 다음 항목
                    link = meta.get("link_el")
                    if link:
                        safe_click(driver, element=link, overlays=OVERLAYS, retries=4, timeout=12)
                    else:
                        save_schedule(meta, {
                            "apply_start": None, "apply_end": None, "result_time": None,
                            "contract_start": None, "contract_end": None
                        })
                        continue

                # 상세에서 공급일정 섹션 추출
                texts, reason = find_supply_schedule(driver, idx, timeout=12, attempts=3)
                if not texts:
                    print(f"공급일정 추출 실패: {reason}")
                    missing_supply_schedule.append((meta.get("name"), reason))

                    # 일정 미확보 시 None으로 저장
                    save_schedule(meta, {
                        "apply_start": None, "apply_end": None, "result_time": None,
                        "contract_start": None, "contract_end": None
                    })
                else:
                    # 표 기반 → 1차 파싱 후 대표 일정 선택
                    if texts["type"] == "table":
                        tparsed = parse_table_lines(texts["table_lines"])
                        parsed = choose_primary(tparsed)

                        # 계약일정이 표에 없고 li에 있으면 보정
                        if (parsed.get("contract_start") is None or parsed.get("contract_end") is None) and texts["li_lines"]:
                            li_fix = parse_li_texts(texts["li_lines"])
                            if parsed.get("contract_start") is None and li_fix.get("contract_start"):
                                parsed["contract_start"] = li_fix["contract_start"]
                            if parsed.get("contract_end") is None and li_fix.get("contract_end"):
                                parsed["contract_end"] = li_fix["contract_end"]

                        save_schedule(meta, parsed)

                    # li 기반 → 바로 파싱 저장
                    else:
                        parsed = parse_li_texts(texts["li_lines"])
                        save_schedule(meta, parsed)

                # 목록으로 복귀(히스토리 불안정 회피용)
                driver.get(LIST_URL)
                dom_ready(driver, timeout=PAGE_WAIT)
                wait_overlay_gone(driver, OVERLAYS, timeout=6)
                wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=15)
                time.sleep(0.3)  # 서버 부하/렌더 타이밍 완화

            # 페이지네이션 처리
            try:
                next_btn = driver.find_element(By.CSS_SELECTOR, "a.page_next")
                cls = (next_btn.get_attribute("class") or "").lower()
                if "disabled" in cls:
                    print("마지막 페이지 도달")
                    break

                # 다음 페이지 이동
                safe_click(driver, element=next_btn, overlays=OVERLAYS, retries=3, timeout=10)
                dom_ready(driver, timeout=PAGE_WAIT)
                wait_overlay_gone(driver, OVERLAYS, timeout=6)
                wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=15)

                # 페이지 전환 전에 누적 전송
                flush_bulk()

            except NoSuchElementException:
                print("다음 버튼 없음, 종료")
                break

        # 마지막 잔여 데이터 전송
        flush_bulk()

        # 실패 목록 로깅
        if missing_supply_schedule:
            print("일부 공고는 공급일정 추출 실패:", missing_supply_schedule)

    finally:
        driver.quit()
