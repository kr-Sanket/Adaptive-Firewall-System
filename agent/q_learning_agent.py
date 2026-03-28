import random


class QLearningAgent:
    """
    Reinforcement Learning agent using Q-Learning.
    Learns optimal firewall decisions.
    """

    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.2):
        self.q_table = {}  # {(state): {action: value}}
        self.actions = actions

        self.alpha = alpha      # Learning rate
        self.gamma = gamma      # Discount factor
        self.epsilon = epsilon  # Exploration rate

    # -----------------------------
    # Ensure state exists in Q-table
    # -----------------------------
    def _initialize_state(self, state):
        if state not in self.q_table:
            self.q_table[state] = {action: 0.0 for action in self.actions}

    # -----------------------------
    # Choose Action (ε-greedy)
    # -----------------------------
    def choose_action(self, state):
        self._initialize_state(state)

        if random.random() < self.epsilon:
            return random.choice(self.actions)  # Explore
        else:
            return max(self.q_table[state], key=self.q_table[state].get)  # Exploit

    # -----------------------------
    # Update Q-value
    # -----------------------------
    def update(self, state, action, reward, next_state):
        self._initialize_state(state)
        self._initialize_state(next_state)

        current_q = self.q_table[state][action]
        max_future_q = max(self.q_table[next_state].values())

        new_q = current_q + self.alpha * (reward + self.gamma * max_future_q - current_q)

        self.q_table[state][action] = new_q
