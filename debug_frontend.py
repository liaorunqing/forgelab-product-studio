from playwright.sync_api import sync_playwright
import time, sys

mode=sys.argv[1] if len(sys.argv)>1 else "structure"

with sync_playwright() as p:
    b=p.chromium.launch(headless=True,channel="chrome")
    page=b.new_page(viewport={"width":1280,"height":900})
    page.on("console",lambda m: print("CONSOLE",m.type,m.text,flush=True))
    page.on("pageerror",lambda e: print("PAGEERROR",e,flush=True))
    page.goto("http://127.0.0.1:8000/?debug=1",wait_until="networkidle")
    page.locator('#fileInput').set_input_files(r'C:\Users\liaoq\AppData\Local\Temp\codex-clipboard-2949bef7-db40-4da6-ba74-9d0e9e666042.png')
    page.locator(f'input[value="{mode}"]').check()
    if mode == "both":
        assert page.locator('#count').input_value() == '3'
    page.locator('#count').select_option('1')
    page.locator('#generateBtn').click()
    for n in range(45):
        time.sleep(3)
        print(n, page.locator('#resultSection').get_attribute('class'), page.locator('#progressBox').get_attribute('class'), page.locator('#toast').inner_text(),flush=True)
        if 'hidden' not in (page.locator('#resultSection').get_attribute('class') or ''): break
    page.screenshot(path=f'debug-frontend-{mode}.png',full_page=True)
    print('RESULT',page.locator('#resultSection').inner_text()[:500],flush=True)
    b.close()
