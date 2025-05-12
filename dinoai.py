
from playwright.sync_api import sync_playwright, Playwright
import pathlib
import time

from qlearning import QLearning
from static_method import StaticMethod
from torch_method import TorchMethod


def reset_state(is_jumping, is_docking, page):
    if is_docking:
        page.keyboard.up("ArrowDown")
    if is_jumping:
        page.keyboard.up("Space")
    return False, False


def run(playwright_passed: Playwright):
    method = TorchMethod()
    filepath = pathlib.Path("dinorunner/index.html").resolve().as_uri()
    chromium = playwright_passed.chromium # or "firefox" or "webkit".
    browser = chromium.launch(headless=False)
    page = browser.new_page()
    page.goto(filepath)
    page.wait_for_selector('div#messageBox') #waits for the page to load
    i = 1
    is_jumping, is_docking = False, False
    while i < 6000000:
        reset_state(is_jumping, is_docking, page)
        if i%10 == 0: # reload the page after few attempts cause of a bug in the game
            page.reload()
            page.wait_for_selector('div#messageBox')  # waits for the page to load
        page.keyboard.press("Space") #starts the game
        crashed = False
        while not crashed:
            time.sleep(1 / 60) #Sleep one frame (FPS = 60)
            obstacle = page.evaluate("""
        Runner.instance_.horizon.obstacles.filter(o => o.xPos + (o.typeConfig.width * o.size) >= Runner.instance_.tRex.xPos).map(o => ({
                x: o.xPos,
                y: o.yPos,
                w: o.typeConfig.width * o.size,
                h: o.typeConfig.height,
                s: Runner.instance_.currentSpeed,
                t: Runner.instance_.time,
                n: performance.now(),
                j: Runner.instance_.tRex.jumping,
                d: Runner.instance_.tRex.ducking,
                r: Runner.instance_.distanceMeter.getActualDistance(Runner.instance_.distanceRan),
                dy: Runner.instance_.tRex.yPos,
                dh: Runner.instance_.tRex.ducking?Runner.instance_.tRex.config.HEIGHT_DUCK:Runner.instance_.tRex.config.HEIGHT
            }))[0];
    """)
            if obstacle is not None:
                is_jumping = obstacle["j"]
                is_docking = obstacle["d"]
                current_action = method.get_move(obstacle, is_jumping, is_docking)
                if current_action == 1:
                    page.keyboard.down("Space")
                elif current_action == 2:
                    page.keyboard.down("ArrowDown")
                else:
                    reset_state(is_jumping, is_docking, page)
                crashed = page.evaluate('Runner.instance_.crashed')
                method.set_reward(obstacle, current_action, crashed, is_jumping, is_docking)
            if crashed:
                print(f"Crashed {i}")
                time.sleep(1)  # Sleep 1 second
                i = i + 1
    browser.close()

if __name__ == '__main__':
    with sync_playwright() as playwright:
        run(playwright)