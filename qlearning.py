from method import Method
import numpy
import math


def get_state(input_state):
    return get_state_from_position(
        input_state['x'],
        input_state['y'],
        input_state['w'],
        input_state['h'],
        input_state['s']
    )

def get_state_from_position(x, y, w, h, s):
    return (
        int(x / 15),
        y,
        w,
        h,
        int(s / 3)
    )

class QLearning(Method):

    def __init__(self):
        self.Q = {}
        self.actions = range(3)
        self.alpha = 0.1
        self.gamma = 0.95

    def get_move(self, input_state):
        state = get_state(input_state)
        return numpy.argmax([self.Q.get((state, a), 0) for a in self.actions])

    def set_reward(self, input_state, action, crashed):
        state = get_state(input_state)
        old_value = self.Q.get((state, action), 0)

        if crashed:
            reward = -100
            future = 0
        else:
            reward = 1  # Or some small positive value
            delta_time = input_state['n'] - input_state['t']
            future_x = math.floor((input_state['s'] * 60 / 1000) * delta_time)
            next_state = get_state_from_position(future_x, input_state['y'], input_state['w'], input_state['h'],
                                                 input_state['s'])
            future = max([self.Q.get((next_state, a), 0) for a in self.actions])

        new_value = old_value + self.alpha * (reward + self.gamma * future - old_value)
        self.Q[(state, action)] = new_value
        pass

