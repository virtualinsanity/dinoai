from abc import ABC, abstractmethod

class Method(ABC):
    @abstractmethod
    def get_move(self, input_state):
        ...

    @abstractmethod
    def set_reward(self, input_state, action, crashed):
        ...