from pathlib import Path
import sys
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8000/?e2e=1"
IMAGE = r"C:\Users\liaoq\AppData\Local\Temp\codex-clipboard-2949bef7-db40-4da6-ba74-9d0e9e666042.png"
OUT = Path("frontend-e2e")
OUT.mkdir(exist_ok=True)

def run_mode(page, mode, expected_min_cards):
    print(f"START {mode}", flush=True)
    page.goto(URL, wait_until="networkidle")
    page.locator("#fileInput").set_input_files(IMAGE)
    page.locator("#count").select_option("1")
    page.locator(f'input[name="mode"][value="{mode}"]').locator("xpath=..").click(timeout=10000)
    print(f"SELECTED {mode}", flush=True)
    if mode == "both":
        assert page.locator("#count").input_value() == "3", "A+B did not enforce at least two outputs"
    page.locator("#generateBtn").click(timeout=10000)
    print(f"SUBMITTED {mode}", flush=True)
    page.locator("#resultSection").wait_for(state="visible", timeout=180000)
    cards = page.locator(".product-card")
    assert cards.count() >= expected_min_cards, (mode, cards.count())
    assert page.locator("#analysisBox").is_visible(), mode
    assert page.locator("#analysisContent").inner_text().strip(), mode
    assert page.locator(".product-image img").count() >= expected_min_cards, mode
    text = cards.nth(0).inner_text()
    page.screenshot(path=str(OUT / f"{mode}.png"), full_page=True)
    print(f"{mode}: cards={cards.count()} first={text[:90].replace(chr(10), ' | ')}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, channel="chrome")
    page = browser.new_page(viewport={"width": 1440, "height": 1050})
    errors=[]
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    run_mode(page, "structure", 1)
    run_mode(page, "feature", 1)
    run_mode(page, "both", 2)
    relevant = [x for x in errors if "favicon" not in x and "404" not in x]
    assert not relevant, relevant
    print("FRONTEND_E2E_OK")
    browser.close()
