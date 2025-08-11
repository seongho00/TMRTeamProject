from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from selenium.webdriver.common.by import By
import time


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
            items = extract_schedule_items(target_h3)
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


def extract_schedule_items(target_h3):
    results = []

    # 2) table 형태 (다음 h3 전까지 모든 table 검색)
    try:
        tables = target_h3.find_elements(
            By.XPATH,
            "following-sibling::*[not(self::h3)]//table"
        )
    except:
        tables = []

    for table in tables:
        rows = table.find_elements(By.XPATH, ".//tbody/tr")
        for row in rows:
            tds = row.find_elements(By.TAG_NAME, "td")
            vals = [td.text.strip() for td in tds if td.text.strip()]
            if vals:
                results.append(" | ".join(vals))

    # 1) li 형태
    lis = target_h3.find_elements(By.XPATH, "following-sibling::*//li")
    results.extend([li.text.strip() for li in lis if li.text.strip()])
    if results:
        return results



    return results


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

        print(f"{idx+1}번째 공고 이름: {name}")
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

        items = extract_schedule_items(target_h3)
        if items:
            for item in items:
                print(item)
        else:
            print(f"⚠ {idx + 1}번째 공고 - 공급일정 데이터 없음")

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

driver.quit()
