from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.by import By
import time
import re
from datetime import datetime
import pymysql


# ====== 대기 함수 ======
def wait_for_elements(driver, by, value, min_count=1, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(by, value)) >= min_count
    )
    return driver.find_elements(by, value)


# 부모 요소 안에서 자식 요소를 기다리는 함수
def wait_for_child_element(parent_element, by, value, timeout=10):
    return WebDriverWait(parent_element, timeout).until(
        lambda el: el.find_element(by, value)
    )


def wait_for_child_elements(parent_element, by, value, min_count=1, timeout=10):
    WebDriverWait(parent_element, timeout).until(
        lambda el: len(el.find_elements(by, value)) >= min_count
    )
    return parent_element.find_elements(by, value)


def find_supply_schedule(driver, idx, timeout=10, attempts=3):
    """
    상세 페이지에서 '공급일정' li들을 찾아 text 리스트로 반환.
    실패하면 (None, reason) 반환.
    """

    def wait_dom_ready():
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )

    def switch_iframe_until_sub_container():
        # 기본 컨텍스트에서 먼저 시도
        try:
            WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.ID, "sub_container")))
            return True
        except TimeoutException:
            pass

        # iframe 순회
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

    last_reason = ""
    for attempt in range(1, attempts + 1):
        try:
            wait_dom_ready()

            # NetFunnel/로딩 레이어가 있다면 사라질 때까지
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

            # sub_container 보장 (기본 또는 iframe)
            ok = switch_iframe_until_sub_container()
            if not ok:
                last_reason = "no #sub_container"
                raise TimeoutException(last_reason)

            # h3.tit1 로드 대기 (동적 렌더링 대비)
            try:
                h3_elements = WebDriverWait(driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#sub_container h3.tit1"))
                )
            except TimeoutException:
                last_reason = "no h3.tit1"
                raise

            # '공급일정' 제목 찾기
            target_h3 = None
            for h in h3_elements:
                if "공급일정" in (h.text or ""):
                    target_h3 = h
                    break

            # 공백/개행 대응 XPath 재시도
            if not target_h3:
                try:
                    target_h3 = driver.find_element(
                        By.XPATH,
                        "//*[@id='sub_container']//h3[contains(@class,'tit1')][contains(normalize-space(.),'공급일정')]"
                    )
                except NoSuchElementException:
                    last_reason = "no '공급일정' heading"
                    raise TimeoutException(last_reason)

            # ✅ li → table 순차 파싱으로 통합
            items = extract_items(target_h3)
            if items:
                return items, None

            last_reason = "no schedule items (li/table)"
            raise TimeoutException(last_reason)


        except (TimeoutException, StaleElementReferenceException) as e:
            # 재시도 전 안정화
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
    (※ 이 프로젝트는 'table+li' 또는 'li-only'만 고려)
    """
    # table 수집
    table_lines = []
    tables = target_h3.find_elements(By.XPATH, "following-sibling::*[not(self::h3)]//table")
    for table in tables:
        for row in table.find_elements(By.XPATH, ".//tbody/tr"):
            tds = [td.text.strip() for td in row.find_elements(By.TAG_NAME, "td")]
            tds = [t for t in tds if t]
            if tds:
                table_lines.append(" | ".join(tds))

    # li 수집
    lis = target_h3.find_elements(By.XPATH, "following-sibling::*//li")
    li_lines = [li.text.strip() for li in lis if li.text.strip()]

    if table_lines:
        return {"type": "table", "table_lines": table_lines, "li_lines": li_lines}
    # table 없으면 무조건 li-only로 취급
    return {"type": "li", "table_lines": [], "li_lines": li_lines}


DT = "%Y.%m.%d %H:%M"
D = "%Y.%m.%d"


def _clean(s: str) -> str:
    # 보이지 않는 공백/비슷한 기호/괄호 제거 등
    s = s.replace("\u00A0", " ").replace("\u200B", "")
    s = s.replace("∼", "~").replace("〜", "~").replace("－", "-")
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\(([^)]*)\)", r"\1", s)  # "(10:00~16:00)" -> "10:00~16:00"
    return s.strip()


def _dt(s: str) -> datetime:
    s = _clean(s)
    if re.search(r"\d{1,2}:\d{2}", s):
        return datetime.strptime(s, DT)
    return datetime.strptime(s, D)


# --- table 전용 파서 ---
def parse_table_lines(lines):
    """
    lines 예:
      '최초입찰 | 2025.07.30 (10:00~16:00) | 2025.07.30 (16:00) | 2025.07.30 (17:00) | 2025.07.30 (18:00)'
      '재입찰   | 2025.07.31 (10:00~16:00) | 2025.07.31 (16:00) | 2025.07.31 (17:00) | 2025.07.31 (18:00)'
      '계약체결일정 : 2025.08.11 ~ 2025.08.12'
    정책:
      - 2번째 칼럼: 날짜 1개 + 시간 2개 → apply_start/end
      - 마지막 칼럼: 개찰결과게시일시(우선). 없으면 그 앞 칼럼(개찰일시)로 폴백
    """
    parsed = {
        "rows": [],  # [{label, apply_start, apply_end, result_time}]
        "contract_start": None,
        "contract_end": None,
    }

    for raw in lines:
        line = raw.strip()
        if not line or "입찰일정" in line:
            continue

        # 계약체결일정
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

        # 2번째 칼럼: 'YYYY.MM.DD (HH:MM~HH:MM)' 류
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

        # result_time: 마지막 칼럼 우선, 없으면 직전 칼럼 폴백
        result_time = None

        def extract_dt_from_col(col_text: str):
            col = _clean(col_text)
            d2 = re.search(r"\d{4}\.\d{1,2}\.\d{1,2}", col)
            if not d2:
                return None
            t2 = re.search(r"\d{1,2}:\d{2}", col)
            return _dt(f"{d2.group()} {t2.group() if t2 else '00:00'}")

        if len(parts) >= 2:
            # 우선: 마지막 칼럼(개찰결과게시일시)
            result_time = extract_dt_from_col(parts[-1])

        if result_time is None and len(parts) >= 3:
            # 폴백: 뒤에서 두 번째(개찰일시)
            result_time = extract_dt_from_col(parts[-2])

        parsed["rows"].append({
            "label": label,
            "apply_start": apply_start,
            "apply_end": apply_end,
            "result_time": result_time
        })

    return parsed


def choose_primary(parsed_table):
    """
    정책:
      - 신청구간: '최초' 라벨 우선, 없으면 가장 이른 시작
      - 결과시간: 같은 라벨 행 우선, 없으면 가장 이른 결과시간
    """
    rows = [r for r in parsed_table["rows"] if r["apply_start"] and r["apply_end"]]
    result = {"apply_start": None, "apply_end": None, "result_time": None,
              "contract_start": parsed_table["contract_start"], "contract_end": parsed_table["contract_end"]}

    chosen = None
    if rows:
        firsts = [r for r in rows if str(r["label"]).startswith("최초")]
        chosen = firsts[0] if firsts else sorted(rows, key=lambda x: x["apply_start"])[0]
        result["apply_start"] = chosen["apply_start"]
        result["apply_end"] = chosen["apply_end"]

    # result_time 선택
    rts = [r for r in parsed_table["rows"] if r["result_time"]]
    if rts:
        if chosen:
            same = [r for r in rts if r["label"] == chosen["label"]]
            result["result_time"] = (same[0]["result_time"] if same
                                     else sorted(rts, key=lambda x: x["result_time"])[0]["result_time"])
        else:
            result["result_time"] = sorted(rts, key=lambda x: x["result_time"])[0]["result_time"]

    return result


# --- li 전용 파서 ---
def parse_li_texts(texts):
    data = {"apply_start": None, "apply_end": None, "result_time": None, "contract_start": None, "contract_end": None}

    for raw in texts:
        txt = _clean(raw)  # 괄호/이후 제거 + 공백 정리

        # 신청일시 : YYYY.MM.DD HH:MM ~ (YYYY.MM.DD )?HH:MM
        m = re.search(
            r"^신청일시\s*:\s*(\d{4}\.\d{1,2}\.\d{1,2})\s*(\d{1,2}:\d{2})\s*[~\-]\s*(?:(\d{4}\.\d{1,2}\.\d{1,2})\s*)?(\d{1,2}:\d{2})",
            txt
        )
        if m:
            d1, t1, d2_opt, t2 = m.groups()
            d2 = d2_opt or d1  # 끝 날짜가 없으면 시작 날짜로 상속
            data["apply_start"] = _dt(f"{d1} {t1}")
            data["apply_end"] = _dt(f"{d2} {t2}")
            continue

        # 결과발표일시 / 개찰결과게시일시 : YYYY.MM.DD (HH:MM)
        m = re.search(
            r"^(?:결과발표일시|개찰결과게시일시)\s*:\s*(\d{4}\.\d{1,2}\.\d{1,2})(?:\s*(\d{1,2}:\d{2}))?",
            txt
        )
        if m:
            d, t = m.groups()
            data["result_time"] = _dt(f"{d} {t or '00:00'}")
            continue

        # 계약체결일정 : YYYY.MM.DD ~ YYYY.MM.DD
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
    password="",
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
  update_date=CURRENT_TIMESTAMP
"""


# ====== 데이터 저장 함수 ======
def save_schedule(name, parsed):
    cursor.execute(UPSERT_SQL, (
        name,
        parsed.get("apply_start"),
        parsed.get("apply_end"),
        parsed.get("result_time"),
        parsed.get("contract_start"),
        parsed.get("contract_end"),
    ))
    conn.commit()  # 바로 반영 (원하면 페이지 끝나고 한 번만 커밋 가능)


missing_supply_schedule = []  # 공급일정 없는 공고 번호 저장 리스트

# ====== 크롤링 시작 ======
driver = webdriver.Chrome(service=Service("chromedriver.exe"))
driver.get("https://apply.lh.or.kr/lhapply/apply/wt/wrtanc/selectWrtancList.do?mi=1069")

# 목록 로드 대기
wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=15)

# 페이지당 모든 공고 순회
while True:
    rows = wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=10)

    for idx in range(len(rows)):
        # 매 클릭 전에 다시 목록 요소 새로 가져오기 (stale 방지)
        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        link = rows[idx].find_element(By.CSS_SELECTOR, "a")
        span = link.find_element(By.CSS_SELECTOR, "span")
        name = span.text.strip()

        print(f"{idx + 1}번째 공고 이름: {name}")
        old = driver.current_url
        link.click()

        # 상세 페이지 로드 대기 (상세 페이지 고유 요소로 바꾸기)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "table, .view, .detail"))
        )

        texts, reason = find_supply_schedule(driver, idx, timeout=10, attempts=3)
        if not texts:
            print(f"⚠ {idx + 1}번째 공고 - 공급일정 추출 실패: {reason}")
            missing_supply_schedule.append((idx + 1, reason))

        try:
            h3_elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#sub_container h3.tit1"))
            )
        except TimeoutException:
            print(f"⚠ {idx + 1}번째 공고 - #sub_container h3.tit1 없음, 건너뜀")
            missing_supply_schedule.append(idx + 1)
            driver.back()
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr"))
            )
            continue

        target_h3 = None
        for h in h3_elements:
            if "공급일정" in (h.text or ""):
                target_h3 = h
                break

        if not target_h3:
            print(f"⚠ {idx + 1}번째 공고 - 공급일정 제목 없음, 건너뜀")
            missing_supply_schedule.append(idx + 1)
            driver.back()
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr"))
            )
            continue

        data = extract_items(target_h3)

        if data["type"] == "table":
            # ✅ 키 이름 수정: data["table_lines"]
            tparsed = parse_table_lines(data["table_lines"])
            parsed  = choose_primary(tparsed)

            # ✅ table에서 계약일정이 비면 li로 보강 (data["li_lines"])
            if (parsed.get("contract_start") is None or parsed.get("contract_end") is None) and data["li_lines"]:
                li_fix = parse_li_texts(data["li_lines"])
                if parsed.get("contract_start") is None and li_fix.get("contract_start"):
                    parsed["contract_start"] = li_fix["contract_start"]
                if parsed.get("contract_end") is None and li_fix.get("contract_end"):
                    parsed["contract_end"] = li_fix["contract_end"]

            save_schedule(name, parsed)
            print("DB saved (table):", name, parsed)

        elif data["type"] == "li":
            # ✅ 키 이름 수정: data["li_lines"]
            parsed = parse_li_texts(data["li_lines"])
            save_schedule(name, parsed)
            print("DB saved (li):", name, parsed)
        else:
            print(f"⚠ {idx + 1} - 공급일정 데이터 없음")

        # 상세 페이지에서 데이터 추출 예시

        WebDriverWait(driver, 10).until(lambda d: d.current_url != old)

        # 뒤로 가기
        driver.back()

        # 다시 목록 로드 대기
        wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=10)
        print("-----------------------------")
        time.sleep(0.5)  # 서버 부하 방지

    # 페이지네이션: 다음 버튼 클릭
    try:
        next_btn = driver.find_element(By.CSS_SELECTOR, "a.page_next")
        if "disabled" in next_btn.get_attribute("class"):
            print("📌 마지막 페이지 도달")
            break
        next_btn.click()
        wait_for_elements(driver, By.CSS_SELECTOR, "table tbody tr", min_count=1, timeout=10)
    except:
        print("📌 다음 버튼 없음, 종료")
        break

cursor.close()
conn.close()
driver.quit()
