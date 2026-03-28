import random
from environment.adaptive_attacker import AdaptiveAttacker


class MultiAttackerEnvironment:
    """
    Simulates multiple independent attackers with varied profiles.
    Some are aggressive, some are patient and stealthy.
    """

    def __init__(self, num_attackers=3):
        profiles = [
            # Aggressive attacker — high aggression, starts confident
            {"aggression": random.uniform(0.7, 0.9), "start_confidence": 0.6},
            # Patient attacker — medium aggression, starts cautious
            {"aggression": random.uniform(0.3, 0.5), "start_confidence": 0.2},
            # Opportunistic attacker — varies
            {"aggression": random.uniform(0.4, 0.7), "start_confidence": 0.35},
        ]

        self.attackers = []
        for p in profiles[:num_attackers]:
            attacker = AdaptiveAttacker(aggression=p["aggression"])
            attacker.confidence = p["start_confidence"]  # set starting confidence
            self.attackers.append(attacker)

    def step(self, defender_actions):
        activities = []
        for attacker, action in zip(self.attackers, defender_actions):
            activity = attacker.generate_activity()
            attacker.update_strategy(action)
            activities.append((attacker, activity))
        return activities