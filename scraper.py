from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def get_download_page():
    url = "https://www.nvidia.com/en-us/geforce/game-ready-drivers/"
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()

        page = context.new_page()
        page.goto(url)
        html = page.content()

        context.close()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    download_page = soup.select('a#DsktpGrdDwnldBtn')

    # the href attribute contains a relative link /en-us/..... which is why i'm adding https://nvidia.com
    return f"https://nvidia.com{download_page[0]['href']}" 

def get_link(url):
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        
        page = context.new_page()
        page.goto(url)
        html = page.content()

        context.close()
        browser.close()

    soup = BeautifulSoup(html, 'html.parser')
    download_link = soup.select('a#agreeDownload-243341')
    
    return download_link[0]['href']

try:
    download_page = get_download_page()
    link = get_link(download_page)

    if link:
        print(link)
    else:
        print("Error")
except:
    print("Error")