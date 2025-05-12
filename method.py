from abc import ABC, abstractmethod

class Method(ABC):
    @abstractmethod
    def get_move(self, input_state, is_jumping, is_docking):
        ...

    @abstractmethod
    def set_reward(self, input_state, action, crashed, is_jumping, is_docking):
        ...