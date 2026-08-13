from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="chrome")
    page = browser.new_page(viewport={"width": 1440, "height": 1000})
    errors = []
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto("http://127.0.0.1:8000", wait_until="networkidle")
    assert page.locator("h1").inner_text() == "上传一个玩具，\n直接拿到新产品。"
    assert page.locator("#generateBtn").is_disabled()
    page.locator("#fileInput").set_input_files(
        r"C:\Users\liaoq\AppData\Local\Temp\codex-clipboard-2949bef7-db40-4da6-ba74-9d0e9e666042.png"
    )
    assert not page.locator("#generateBtn").is_disabled()
    assert page.locator("#preview").is_visible()
    assert page.locator(".workbench").evaluate("e => getComputedStyle(e).backgroundColor") == "rgb(250, 249, 245)"
    assert page.locator(".input-tab").count() == 2
    assert page.locator("input[name=mode]").count() == 3
    page.locator('[data-input="text"]').click()
    page.locator("#productDescription").fill("一个会根据卡片节奏扇动翅膀并播放声音的儿童桌面小鸟玩具。")
    assert not page.locator("#generateBtn").is_disabled()
    page.screenshot(path="ui-test.png", full_page=True)
    assert not [e for e in errors if "404" not in e], errors
    print("UI_OK title/upload/preview/api-status")
    browser.close()
