import random
from collections import deque
import numpy as np


class ReplayBuffer:
    """
    Stores past experiences so the agent learns from mixed history
    (prevents unstable learning).
    """

    def __init__(self, capacity=5000):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state):
        self.buffer.append((state, action, reward, next_state))

    def sample(self, batch_size=32):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states = zip(*batch)

        return (
            np.array(states, dtype=np.float32),
            actions,
            rewards,
            np.array(next_states, dtype=np.float32)
        )

    def __len__(self):
        return len(self.buffer)
