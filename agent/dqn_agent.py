import torch
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np

class DQN(nn.Module):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Linear(64, output_dim)
        )

    def forward(self, x):
        return self.net(x)


class DQNAgent:
    def __init__(self, state_dim, actions):
        self.actions = actions
        self.model = DQN(state_dim, len(actions))
        self.optimizer = optim.Adam(self.model.parameters(), lr=1e-3)
        self.loss_fn = nn.MSELoss()
        self.epsilon = 1.0        # start exploring heavily
        self.epsilon_min = 0.05
        self.epsilon_decay = 0.995


    def act(self, state):
        if random.random() < self.epsilon:
            return random.choice(range(len(self.actions)))

        with torch.no_grad():
            q = self.model(torch.tensor(state, dtype=torch.float32))
            return torch.argmax(q).item()
    
    def decay_exploration(self):
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def train_batch(self, states, actions, rewards, next_states):
        states = torch.tensor(states, dtype=torch.float32)
        next_states = torch.tensor(next_states, dtype=torch.float32)
        rewards = torch.tensor(rewards, dtype=torch.float32)

        q_values = self.model(states)
        next_q = self.model(next_states).detach()

        target = q_values.clone().detach()

        for i, action in enumerate(actions):
            target[i, action] = rewards[i] + 0.9 * torch.max(next_q[i])

        loss = self.loss_fn(q_values, target)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        # -----------------------------
    # Save trained model
    # -----------------------------
    def save(self, path="models/dqn_firewall.pt"):
        torch.save(self.model.state_dict(), path)

    # -----------------------------
    # Load trained model
    # -----------------------------
    def load(self, path="models/dqn_firewall.pt"):
        self.model.load_state_dict(torch.load(path))
        self.model.eval()
