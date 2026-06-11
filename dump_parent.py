from playwright.sync_api import sync_playwright

url = 'https://sports.tipico.de/de/alle/fussball/wm-wetten'
js = """
() => {
    let matches = document.querySelectorAll('a[href*="/event/"]');
    if(matches.length === 0) return "No matches";
    let firstMatch = matches[0];
    let parent = firstMatch.parentElement.parentElement.parentElement;
    return parent.innerHTML.substring(0, 1000);
}
"""

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(url)
    page.wait_for_timeout(4000)
    html = page.evaluate(js)
    print(html)
