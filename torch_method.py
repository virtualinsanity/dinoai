import torch
import torch.nn as nn
import torch.nn.functional as F

from method import Method
import random
from collections import deque
import math


def get_state(input_state):
    return (
        input_state['x'],
        input_state['y'],
        input_state['w'],
        input_state['h'],
        input_state['s'],
        input_state['dy'],
        input_state['dh']
    )

def find_last_move(memory):
    was_jumping = False
    was_docking = False
    for index, (state, action_taken, is_jumping, is_docking) in memory:
        if index == 0:
            if is_jumping:
                was_jumping = True
            elif is_docking:
                was_docking = True
            else:
                return 10000
        else:
            if (was_jumping and not is_jumping) or (was_docking and not is_docking):
                return index
    return 10000



class DinoNet(nn.Module):
    def __init__(self, input_size=7, output_size=3, hidden_size=32):
        super(DinoNet, self).__init__()
        self.fc1 = nn.Linear(input_size, hidden_size)
        self.fc2 = nn.Linear(hidden_size, hidden_size)
        self.out = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        return torch.clamp(self.out(x), -200, 200)

class TorchMethod(Method):
    def __init__(self):
        self.model = DinoNet()
        self.best_score = 0
        self.average_score = 0
        self.runs = 0
        self.epsilon = 1.0
        self.load_best_model()
        self.memory = deque(maxlen=10000)
        self.optimizer = torch.optim.Adam(self.model.parameters(), lr=0.0001)
        self.last_x = None
        self.num_obstacle = 0
        self.last_score = 0

    def load_best_model(self):
        try:
            checkpoint = torch.load("best_dino_model.pth")
            self.model.load_state_dict(checkpoint['model_state_dict'])
            self.best_score = checkpoint['best_score']
            self.average_score = checkpoint['average_score']
            self.runs = checkpoint['runs']
            self.epsilon = checkpoint['epsilon']
            print(f"✅ Loaded best model with score {self.best_score} average_score {self.average_score} runs {self.runs} epsilon {self.epsilon}")
        except FileNotFoundError:
            print("⚠️ No checkpoint found.")

    def get_move(self, input_state, is_jumping, is_docking):
        if random.random() < self.epsilon: #generate a random move
            if is_jumping:
                return random.randint(0, 1) # if jumping the only moves allowed are stop jumping or continue jumping
            elif is_docking:
                return 0 if random.randint(0, 1) == 0 else 2 # if docking, the only moves allowed are stop or contnue docking
            else:
                return random.randint(0, 2) # otherwise all moves are valid
        with torch.no_grad(): #return a move from the Neural Network
            computed_state_tensor = self.model(torch.FloatTensor(get_state(input_state)))
            move = torch.argmax(computed_state_tensor).item()  # Returns the action with the biggest reward
            print(f"Current state {computed_state_tensor} move {move}")
            return move

    def set_reward(self, input_state, action_taken, crashed, is_jumping, is_docking):
        self.memory.append((
            get_state(input_state),
            action_taken,
            is_jumping,
            is_docking
            )
        ) #append the current state and action in the memory
        if self.last_x is not None and input_state['x'] > self.last_x: #obstacole successfully skipped
            self.num_obstacle += 1
            self.train(crashed, score = input_state['r']) #train the NN passing the current score
        self.last_x = input_state['x']
        if crashed:
            self.train(crashed) #train the NN
            self.average_score = (self.average_score * self.runs + input_state['r']) / (self.runs + 1)
            print(f" --- last score {self.last_score} average_score {self.average_score} ----")
            self.last_x = None
            self.last_score = 0
            self.runs += 1
            self.epsilon -= 0.001
            self.epsilon = max(self.epsilon, 0.0)

    def train(self, crashed, score = 0):
        reversed_index_memory = enumerate(reversed(self.memory))
        list_memory = list(reversed_index_memory)
        last_move_index = find_last_move(list_memory) #Search for the index of the move that made the dino skip the obstacle
        for index, (state, action_taken, is_jumping, is_docking) in list_memory:
            state_tensor = torch.FloatTensor(state)
            if crashed:
                if index >= 5:
                    break
                target = -100 * (0.9 ** index)
            else:
                if index == last_move_index:
                    # This was the critical move — high reward
                    target = 10 * (score - self.last_score)
                elif is_jumping and action_taken == 1:
                    # Other jump moves – discourage
                    target = -10
                else:
                    # No reward/punishment for neutral actions
                    break
            predicted = self.model(state_tensor)[action_taken].unsqueeze(0)
            target_tensor = torch.tensor([target], dtype=predicted.dtype, device=predicted.device)
            # Compute the loss
            loss = F.smooth_l1_loss(predicted, target_tensor)

            # Optimize the model
            self.optimizer.zero_grad()
            loss.backward()
            self.optimizer.step()

        if not crashed and score > self.average_score:
            print(f"New best score: {score}, saving model.")
            self.save_model(score)

        self.last_score = score
        self.memory.clear()

    def save_model(self, score):
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'best_score': score,
            'average_score': self.average_score,
            'runs': self.runs,
            'epsilon': self.epsilon
        }, "best_dino_model.pth")

        self.best_score = score


