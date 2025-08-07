from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pymysql
from datetime import datetime
import re

# DB 연결
conn = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    db='TMRTeamProject',
    charset='utf8mb4'
)
cursor = conn.cursor()


def save_to_db(data):
    sql = """
    INSERT INTO commercial_property (
        reg_date, update_date,
        article_no, price_type, price, location,
        area_contract, area_real, floor_info, move_in_date,
        management_fee, parking, heating, purpose,
        use_approval_date, toilet_count, broker_name,
        broker_ceo, broker_address, broker_phone
    )
    VALUES (
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s, %s, %s,
        %s, %s
    )
    """
    now = datetime.now()
    values = (
        now, now,  # reg_date, update_date
        data["article_no"], data["price_type"], data["price"], data["location"],
        data["area_contract"], data["area_real"], data["floor_info"], data["move_in_date"],
        data["management_fee"], data["parking"], data["heating"], data["purpose"],
        data["use_approval_date"], data["toilet_count"], data["broker_name"],
        data["broker_ceo"], data["broker_address"], data["broker_phone"]
    )
    cursor.execute(sql, values)
    conn.commit()


# 면적 숫자 처리
def parse_area(text):
    match = re.match(r"([\d\.]+)㎡/([\d\.]+)㎡", text)
    if match:
        contract = float(match.group(1))
        real = float(match.group(2))
        return {"contract": contract, "real": real}
    return {"contract": 0, "real": 0}


# 관리비용 전처리함수
def parse_management_fee(fee_str):
    if not fee_str or "없음" in fee_str:
        return 0

    fee_str = fee_str.replace(" ", "").replace(",", "")

    if "만원" in fee_str:
        num_part = fee_str.replace("만원", "")
        try:
            return int(float(num_part) * 10000)
        except:
            return 0
    else:
        # 숫자만 있을 경우 그냥 int로 변환
        try:
            return int(fee_str)
        except:
            return 0


# ⛳ 유틸 함수
def wait_for_element(driver, by, value, timeout=10):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((by, value))
    )


def wait_for_elements(driver, by, value, min_count=1, timeout=10):
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(by, value)) >= min_count
    )
    return driver.find_elements(by, value)


def wait_for_child_element(parent_element, by, value, timeout=10):
    return WebDriverWait(parent_element, timeout).until(
        lambda el: el.find_element(by, value)
    )


# ✅ 크롬 드라이버 설정
driver = webdriver.Chrome()
driver.get("https://new.land.naver.com/offices?ms=37.52139,126.931083,16&a=SG&e=RETAIL")
time.sleep(3)

# ✅ 스크롤 대상 지정
scroll_target = driver.find_element(By.CSS_SELECTOR, "div.item_list.item_list--article")
scroll_pause = 1

# ✅ 중복 방지용 집합
seen_items = set()

# ✅ 매물 처리 루프
while True:
    # 현재 화면에 보이는 매물들
    item_divs = driver.find_elements(By.CSS_SELECTOR, "div.item")
    new_items_found = False

    for item in item_divs:
        try:
            identifier = item.text.strip()
            if identifier in seen_items:
                continue

            new_items_found = True
            seen_items.add(identifier)

            # 스크롤 이동 후 클릭
            driver.execute_script("arguments[0].scrollIntoView(true);", item)
            time.sleep(0.2)
            item.click()

            # 상세 정보 대기 및 추출
            price_box = wait_for_element(driver, By.CSS_SELECTOR, "div.info_article_price")
            price_type = price_box.find_element(By.CLASS_NAME, "type").text  # ex) 월세
            price_value = price_box.find_element(By.CLASS_NAME, "price").text  # ex) 4,000/230

            # 상세 패널 내 테이블 요소
            detail_table = wait_for_element(driver, By.CSS_SELECTOR, "table.info_table_wrap")
            rows = detail_table.find_elements(By.CSS_SELECTOR, "tr.info_table_item")

            # 원하는 정보 저장용 dict
            detail_info = {}

            for row in rows:
                try:
                    ths = row.find_elements(By.TAG_NAME, "th")
                    tds = row.find_elements(By.TAG_NAME, "td")

                    # ⛔ '매물설명' 행은 건너뛰기
                    if any("매물설명" in th.text for th in ths):
                        continue


                    for th, td in zip(ths, tds):
                        broker_name = ""
                        broker_ceo = ""
                        broker_address = ""
                        broker_phone = ""

                        key = th.text.strip()
                        val = td.text.strip()

                        detail_info[key] = val
                        if key == "중개사":
                            broker_info_elem = row.find_element(By.CSS_SELECTOR, "div.table_td_agent")

                            # 중개사명
                            broker_name = broker_info_elem.find_element(By.CSS_SELECTOR,
                                                                        "strong.info_title").text.strip()

                            # dl 리스트 순회
                            dls = broker_info_elem.find_elements(By.CSS_SELECTOR, "dl.info_agent")
                            for dl in dls:
                                try:
                                    dt = dl.find_element(By.TAG_NAME, "dt").text.strip()
                                    dd = dl.find_element(By.TAG_NAME, "dd").text.strip()

                                    if "대표" in dt:
                                        broker_ceo = dd
                                    elif "소재지" in dt:
                                        broker_address = dd
                                    elif "전화" in dt:
                                        broker_phone = dd
                                except:
                                    continue

                            # 저장
                            detail_info["중개사명"] = broker_name
                            detail_info["대표자"] = broker_ceo
                            detail_info["중개사소재지"] = broker_address
                            detail_info["전화번호"] = broker_phone
                except:
                    continue

            print("📋 상세 정보:")
            for k, v in detail_info.items():
                print(f" - {k}: {v}")

                print(f"📌 매물: {price_type} / {price_value}")

            article_no = detail_info.get("매물번호", "")
            if not article_no:
                continue
            if article_no in seen_items:
                print(f"⚠️ 중복 매물 스킵: {article_no}")
                continue
            seen_items.add(article_no)
            
            mapped_data = {
                "article_no": detail_info.get("매물번호", ""),
                "price_type": price_type,
                "price": price_value,
                "location": detail_info.get("소재지", ""),
                "area_contract": parse_area(detail_info.get("계약/전용면적", "")).get("contract", 0),
                "area_real": parse_area(detail_info.get("계약/전용면적", "")).get("real", 0),
                "floor_info": detail_info.get("해당층/총층", ""),
                "move_in_date": detail_info.get("입주가능일", ""),
                "management_fee": detail_info.get("월관리비", ""),
                "parking": f"{detail_info.get('주차가능여부', '')} / {detail_info.get('총주차대수', '')}",
                "heating": detail_info.get("난방(방식/연료)", ""),
                "purpose": detail_info.get("건축물 용도", ""),
                "use_approval_date": detail_info.get("사용승인일", ""),
                "toilet_count": detail_info.get("화장실 수", ""),
                "broker_name": detail_info.get("중개사명", ""),
                "broker_ceo": detail_info.get("대표자", ""),
                "broker_address": detail_info.get("중개사소재지", ""),
                "broker_phone": detail_info.get("전화번호", "")
            }
            save_to_db(mapped_data)

        except Exception as e:
            print(f"[❌ 오류] 매물 클릭 또는 추출 실패: {e}")
            continue

    if not new_items_found:
        print("✅ 더 이상 새 매물 없음. 종료.")
        break

    # 스크롤을 조금씩 내려 추가 매물 유도
    driver.execute_script("arguments[0].scrollTop += 800", scroll_target)
    time.sleep(scroll_pause)

print(f"🎉 총 크롤링한 매물 수: {len(seen_items)}")
driver.quit()
