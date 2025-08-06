import sys
import json
import io
import re
from playwright.sync_api import sync_playwright

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def scrape_properties(dong_code: str):
    """주어진 동 코드를 사용하여 네이버 부동산 매물을 스크래핑합니다."""
    results = []
    url = f"https://new.land.naver.com/offices?cortarNo={dong_code}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        try:
            page.goto(url, timeout=30000)
            page.wait_for_selector("div.item_list > div > div > div.item", timeout=15000)
            items = page.query_selector_all("div.item_list > div > div > div.item")

            for item in items:
                # 이미지 URL 추출 ---
                image_url = "https://via.placeholder.com/150x120.png?text=No+Image" # 기본 이미지
                thumbnail_element = item.query_selector(".thumbnail")
                if thumbnail_element:
                    style_attr = thumbnail_element.get_attribute("style")
                    if style_attr and "url(" in style_attr:
                        match = re.search(r'url\("?([^")]+)"?\)', style_attr)
                        if match:
                            extracted_url = match.group(1)
                            if extracted_url.startswith("//"):
                                image_url = "https:" + extracted_url
                            else:
                                image_url = extracted_url
                # --- 이미지 추출 끝 ---

                title_element = item.query_selector(".item_title .text")
                title = title_element.inner_text() if title_element else "제목 없음"

                trade_type_element = item.query_selector(".price_line .type")
                trade_type = trade_type_element.inner_text() if trade_type_element else ""

                price_element = item.query_selector(".price_line .price")
                price = price_element.inner_text().replace(" ", "") if price_element else ""

                prop_type_element = item.query_selector(".info_area .line .type")
                prop_type = prop_type_element.inner_text() if prop_type_element else ""

                spec_elements = item.query_selector_all(".info_area .line .spec")
                spec = spec_elements[0].inner_text() if len(spec_elements) > 0 else ""
                description = spec_elements[1].inner_text() if len(spec_elements) > 1 else "설명 없음"

                tags = ", ".join([tag.inner_text() for tag in item.query_selector_all(".tag_area .tag")])

                results.append({
                    "imageUrl": image_url,
                    "title": title,
                    "tradeType": trade_type,
                    "price": price,
                    "type": prop_type,
                    "spec": spec,
                    "description": description,
                    "tags": tags,
                })
        except Exception as e:
            # 오류 발생 시
            print(f"크롤링 중 오류 발생: {e}", file=sys.stderr)
            pass
        finally:
            browser.close()

    print(json.dumps(results, ensure_ascii=False))

if __name__ == "__main__":
    if len(sys.argv) > 1:
        dong_code_arg = sys.argv[1]
        scrape_properties(dong_code_arg)
    else:
        print(json.dumps([]))