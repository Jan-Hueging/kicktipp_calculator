from playwright.sync_api import sync_playwright

url = 'https://sports.tipico.de/de/alle/fussball/wm-wetten'
js = """
() => {
    let els = document.querySelectorAll('header, a[href*="/event/"], a[href*="/teams/"]');
    return Array.from(els).map(e => e.tagName + ': ' + e.innerText.replace(/\\n/g, ' ')).slice(0, 50);
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(4000)
    texts = page.evaluate(js)
    for t in texts:
        print(t)
