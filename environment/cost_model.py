class DefenseCostModel:
    COSTS = {
        "ALLOW":    1,
        "BLOCK":    9,    # was 6 — increased, service disruption is costly
        "THROTTLE": 4,
        "OBSERVE":  1,    # was 2 — cheaper, encourage intelligence gathering
        "DECEIVE":  3     # was 5 — cheaper, encourage strategic deception
    }

    def get_cost(self, action):
        return self.COSTS.get(action, 1)