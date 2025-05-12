from method import Method


class StaticMethod(Method):
    def __init__(self):
        self.last_x = None
        self.num_obstacle = 0
    def set_reward(self, input_state, action, crashed, is_jumping, is_docking):
        if self.last_x is None or input_state['x'] > self.last_x:
            self.num_obstacle += 1
            print(f'obstacle number {self.num_obstacle} current x {input_state} last x {self.last_x}')
        self.last_x = input_state['x']

    def get_move(self, input_state, is_jumping, is_docking):
        if input_state['y'] + input_state['h'] == 140:
            if (input_state['s']*20)+7 > input_state['x'] + input_state['w']:
                return 1
        else:
            if input_state['x'] < 100:
                return 2
        return 0