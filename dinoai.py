from playwright.sync_api import sync_playwright, Playwright
import pathlib
import time
import numpy
import math

Q = {}
actions = range(3)
def run(playwright: Playwright):
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
                current_action = get_move(obstacle)
                if current_action == 1:
                    page.keyboard.press("Space")
                elif current_action == 2:
                    page.keyboard.press("ArrowDown")
                crashed = page.evaluate('Runner.instance_.crashed')
                set_reward(obstacle, current_action, crashed)
            if crashed:
                print(f"Crashed {i}")
                time.sleep(1)  # Sleep 1 second
                i = i + 1
    browser.close()

def get_move(input_state):
    state = get_state(input_state)
    return numpy.argmax([Q.get((state, a), 0) for a in actions])

def set_reward(input_state, action, crashed):
    reward = -100
    state = get_state(input_state)
    old_value = Q.get((state, action), 0)
    if not crashed:
        delta_time = input_state['n'] - input_state['t']
        future_x = math.floor((input_state['s'] * 60 / 1000) * delta_time)
        future = Q.get((int(future_x / 15), input_state['y'], input_state['w'], input_state['h'], int(input_state['s'] / 3), action), 0)
        reward = 0.95 * (1 + 0.1 * future - old_value)
    Q[(state, action)] = old_value + reward
def get_state(input_state):
    return (
        int(input_state['x'] / 15),
        input_state['y'],
        input_state['w'],
        input_state['h'],
        int(input_state['s'] / 3)
    )


with sync_playwright() as playwright:
    run(playwright)