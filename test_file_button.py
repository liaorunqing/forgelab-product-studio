from playwright.sync_api import sync_playwright

FILE=r"C:\Users\liaoq\AppData\Local\Temp\codex-clipboard-2949bef7-db40-4da6-ba74-9d0e9e666042.png"
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True,channel="chrome")
    page=browser.new_page(viewport={"width":1280,"height":900})
    page.goto("http://127.0.0.1:8000/?file-button-test=1",wait_until="networkidle")
    button=page.locator("#chooseFileBtn")
    with page.expect_file_chooser(timeout=5000) as chooser_info:
        button.click(position={"x":button.bounding_box()["width"]/2,"y":button.bounding_box()["height"]/2})
    chooser_info.value.set_files(FILE)
    assert page.locator("#preview").is_visible()
    page.locator("#removeFile").click()
    with page.expect_file_chooser(timeout=5000) as edge_info:
        button.click(position={"x":5,"y":5})
    edge_info.value.set_files(FILE)
    assert page.locator("#preview").is_visible()
    assert page.locator(".workbench").evaluate("e=>getComputedStyle(e).borderRadius") == "24px"
    assert page.locator(".dropzone").evaluate("e=>getComputedStyle(e).borderRadius") == "18px"
    page.screenshot(path="frontend-rounded-tested.png",full_page=True)
    print("FILE_BUTTON_OK center edge preview rounded-layout")
    browser.close()
