from collections import deque
import numpy as np


class BehaviorTracker:
    """
    Maintains short-term history of attacker activity
    so defender can reason over behavior trends.
    """

    def __init__(self, window_size=10):
        self.history = deque(maxlen=window_size)

    def update(self, activity_rate):
        self.history.append(activity_rate)

    def get_features(self):
        """
        Extract behavioral signals from history.
        """

        if len(self.history) == 0:
            return np.zeros(4, dtype=np.float32)

        arr = np.array(self.history)

        mean_rate = np.mean(arr)
        variance = np.var(arr)
        max_rate = np.max(arr)

        # persistence = how often activity stays elevated
        persistence = np.sum(arr > mean_rate) / len(arr)

        return np.array([mean_rate, variance, max_rate, persistence], dtype=np.float32)

