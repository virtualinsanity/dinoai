from playwright.sync_api import sync_playwright, Playwright
import pathlib
import time

def run(playwright: Playwright):
    filepath = pathlib.Path("dinorunner/index.html").resolve().as_uri()
    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(filepath)
    page.wait_for_selector('div#messageBox') #waits for the page to load
    i = 1
    while i < 6:
        page.keyboard.press("Space") #starts the game
        crashed = False
        while not crashed:
            time.sleep(1 / 60) #Sleep one frame (FPS = 60)
            obstacle = page.evaluate("""
        Runner.instance_.horizon.obstacles.map(o => ({
                x: o.xPos,
                y: o.yPos,
                w: o.typeConfig.width * o.size,
                h: o.typeConfig.height
            }))[0];
    """)
            print(f"AI inputs {obstacle}")
            #    #add AI logic here
            crashed = page.evaluate('Runner.instance_.crashed')
            if(crashed):
                print(f"Crashed {i}")
                time.sleep(1)  # Sleep 1 second
                i = i + 1
    browser.close()


with sync_playwright() as playwright:
    run(playwright)