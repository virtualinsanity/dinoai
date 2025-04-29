from playwright.sync_api import sync_playwright, Playwright
import pathlib
import time

from qlearning import QLearning


def run(playwright: Playwright):
    method = QLearning()
    filepath = pathlib.Path("dinorunner/index.html").resolve().as_uri()
    chromium = playwright.chromium # or "firefox" or "webkit".
    browser = chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(filepath)
    page.wait_for_selector('div#messageBox') #waits for the page to load
    i = 1
    while i < 6000000:
        page.keyboard.press("Space") #starts the game
        crashed = False
        while not crashed:
            time.sleep(1 / 60) #Sleep one frame (FPS = 60)
            obstacle = page.evaluate("""
        Runner.instance_.horizon.obstacles.map(o => ({
                x: o.xPos,
                y: o.yPos,
                w: o.typeConfig.width * o.size,
                h: o.typeConfig.height,
                s: Runner.instance_.currentSpeed,
                t: Runner.instance_.time,
                n: performance.now()
            }))[0];
    """)
            if obstacle is not None:
                current_action = method.get_move(obstacle)
                if current_action == 1:
                    page.keyboard.press("Space")
                elif current_action == 2:
                    page.keyboard.press("ArrowDown")
                crashed = page.evaluate('Runner.instance_.crashed')
                method.set_reward(obstacle, current_action, crashed)
            if crashed:
                print(f"Crashed {i}")
                time.sleep(1)  # Sleep 1 second
                i = i + 1
    browser.close()

if __name__ == '__main__':
    with sync_playwright() as playwright:
        run(playwright)