# run_pw_ok.py
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
import os, time

USER_DATA_DIR = "./.chrome-profile"   # 계속 재사용(쿠키/지문 유지)
HEADLESS = False                      # 먼저 창 띄워서 성공여부 확인

def get_env_proxy():
    for k in ("HTTPS_PROXY","https_proxy","HTTP_PROXY","http_proxy"):
        v = os.environ.get(k)
        if v: return {"server": v}
    return None  # 프록시 필요 없으면 None

def main():
    proxy_cfg = get_env_proxy()
    print("[proxy]", proxy_cfg)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            channel="chrome",                # 실제 Chrome 채널
            headless=HEADLESS,
            locale="ko-KR",
            viewport={"width": 1280, "height": 860},
            proxy=proxy_cfg,                 # ★ 회사망이면 필수
            ignore_https_errors=True,        # ★ 사내 MITM 인증서일 때 임시
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run","--no-default-browser-check",
                "--disable-dev-shm-use","--no-sandbox",
            ],
        )
        # 약식 스텔스
        ctx.add_init_script("""
          Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
          Object.defineProperty(navigator, 'language', {get: () => 'ko-KR'});
          Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR','ko','en-US','en']});
          window.chrome = window.chrome || { runtime: {} };
        """)

        page = ctx.new_page()
        try:
            print("[GOTO] root")
            page.goto("https://new.land.naver.com/", wait_until="domcontentloaded", timeout=30000)
            print("[OK] title:", page.title())
        except PwTimeout as e:
            print("[TIMEOUT] root not loaded:", e)
        finally:
            try:
                print("referrer:", page.evaluate("() => document.referrer"))
                print("webdriver:", page.evaluate("() => navigator.webdriver"))
                shot = f"./root_{int(time.time())}.png"
                page.screenshot(path=shot, full_page=True)
                print("[SHOT]", shot)
            except: pass
            ctx.close()

if __name__ == "__main__":
    main()
