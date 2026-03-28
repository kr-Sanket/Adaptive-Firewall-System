import random


class AdaptiveAttacker:
    """
    A persistent, tactically intelligent attacker that:
    - Remembers past failures and adapts
    - Uses multiple strategies per phase
    - Escalates more aggressively when it detects weak defense
    - Doesn't give up easily when blocked
    """

    TACTICS = {
        "RECON": ["slow_scan", "ping_sweep", "passive_listen"],
        "PROBE": ["port_probe", "service_fingerprint", "vuln_test"],
        "EXPLOIT": ["ddos_burst", "brute_force", "payload_inject"],
        "STEALTH": ["low_slow", "encrypted_tunnel", "idle_wait"],
        "ESCALATE": ["privilege_escalate", "lateral_move", "data_exfil"]
    }

    def __init__(self, aggression=0.5):
        self.phase = "RECON"        # Always start in RECON now
        self.confidence = 0.3       # Start lower — must earn escalation
        self.frustration = 0.0
        self.aggression = aggression
        self.blocked_count = 0
        self.success_count = 0
        self.deception_detected = False
        self.consecutive_blocks = 0
        self.total_steps = 0
        self.current_tactic = random.choice(self.TACTICS["RECON"])
        self.persistence = random.uniform(0.6, 1.0)
        self.block_streak = 0
        self.strategy_switch_threshold = random.randint(3, 6)

    def update_strategy(self, defender_action):
        self.total_steps += 1

        if defender_action == "BLOCK":
            self.consecutive_blocks += 1
            self.blocked_count += 1
            self.block_streak += 1

            # Persistent attacker — frustration grows slowly
            self.frustration += 0.05 * (1 - self.persistence)
            self.confidence -= 0.04

            # After hitting block threshold, switch tactic instead of giving up
            if self.block_streak >= self.strategy_switch_threshold:
                self._switch_tactic()
                self.block_streak = 0

        elif defender_action == "DECEIVE":
            # Attacker initially thinks it's succeeding
            self.confidence += 0.12
            self.frustration -= 0.03
            self.consecutive_blocks = 0

            # But over time, attacker may detect deception
            if self.success_count > 5 and random.random() < 0.3:
                self.deception_detected = True
                self.confidence -= 0.2  # realizes it was fooled
                self.frustration += 0.1

        elif defender_action == "THROTTLE":
            self.frustration += 0.02
            self.consecutive_blocks = 0
            # Attacker tries harder when throttled
            self.confidence += 0.03

        elif defender_action == "OBSERVE":
            # Attacker gains confidence when only observed
            self.confidence += 0.08
            self.consecutive_blocks = 0
            self.success_count += 1

        elif defender_action == "ALLOW":
            # Big confidence boost — attacker thinks it's winning
            self.confidence += 0.15
            self.success_count += 1
            self.consecutive_blocks = 0
            self.frustration = max(0, self.frustration - 0.05)

        # Clamp values
        self.confidence = max(0, min(1, self.confidence))
        self.frustration = max(0, min(1, self.frustration))

        self._transition_phase()

    def _switch_tactic(self):
        """
        When blocked repeatedly, attacker switches to a different
        tactic within the same phase — doesn't just give up.
        """
        available = self.TACTICS.get(self.phase, ["passive_listen"])
        self.current_tactic = random.choice(available)

        # Switching tactic recovers some confidence
        self.confidence = min(1.0, self.confidence + 0.1)
        self.frustration = max(0.0, self.frustration - 0.05)

    def _transition_phase(self):
        # Much harder to push into stealth now
        if self.frustration > 0.90 and self.confidence < 0.2:
            self.phase = "STEALTH"
            self.current_tactic = random.choice(self.TACTICS["STEALTH"])

        # New phase: ESCALATE — triggered when attacker is very confident
        elif self.confidence > 0.85:
            self.phase = "ESCALATE"
            self.current_tactic = random.choice(self.TACTICS["ESCALATE"])

        elif self.confidence > 0.70:
            self.phase = "EXPLOIT"
            self.current_tactic = random.choice(self.TACTICS["EXPLOIT"])

        elif self.confidence > 0.45:
            self.phase = "PROBE"
            self.current_tactic = random.choice(self.TACTICS["PROBE"])

        else:
            self.phase = "RECON"
            self.current_tactic = random.choice(self.TACTICS["RECON"])

    def generate_activity(self):
        base = int(60 + self.aggression * 250)

        # Deception-aware attacker behaves more erratically
        noise = random.randint(-20, 20) if self.deception_detected else 0

        if self.phase == "RECON":
            return {
                "rate": random.randint(30, base - 20) + noise,
                "type": self.current_tactic,
                "failed_logins": 0
            }

        if self.phase == "PROBE":
            return {
                "rate": random.randint(base - 10, base + 60) + noise,
                "type": self.current_tactic,
                "failed_logins": random.randint(1, 3)
            }

        if self.phase == "EXPLOIT":
            return {
                "rate": random.randint(base + 100, base + 300) + noise,
                "type": self.current_tactic,
                "failed_logins": random.randint(5, 15)
            }

        if self.phase == "ESCALATE":
            # Most dangerous — high rate, many failed logins, erratic
            return {
                "rate": random.randint(base + 250, base + 500) + noise,
                "type": self.current_tactic,
                "failed_logins": random.randint(10, 30)
            }

        if self.phase == "STEALTH":
            return {
                "rate": random.randint(20, 60) + noise,
                "type": self.current_tactic,
                "failed_logins": 0
            }

        return {"rate": 50, "type": "unknown", "failed_logins": 0}