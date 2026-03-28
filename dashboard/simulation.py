import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
import time
import random
from environment.multi_attacker_env import MultiAttackerEnvironment
from environment.behavior_tracker import BehaviorTracker
from environment.cost_model import DefenseCostModel
from agent.dqn_agent import DQNAgent

ACTIONS = ["ALLOW", "BLOCK", "THROTTLE", "OBSERVE", "DECEIVE"]

PHASE_ENCODING = {
    "RECON":    [1, 0, 0, 0, 0],
    "PROBE":    [0, 1, 0, 0, 0],
    "EXPLOIT":  [0, 0, 1, 0, 0],
    "ESCALATE": [0, 0, 0, 1, 0],
    "STEALTH":  [0, 0, 0, 0, 1],
}

PHASE_COLORS = {
    "RECON":    "#3b82f6",
    "PROBE":    "#f59e0b",
    "EXPLOIT":  "#f97316",
    "ESCALATE": "#ef4444",
    "STEALTH":  "#6b7280",
}

ACTION_COLORS = {
    "ALLOW":    "#22c55e",
    "BLOCK":    "#ef4444",
    "THROTTLE": "#f59e0b",
    "OBSERVE":  "#3b82f6",
    "DECEIVE":  "#a855f7",
}

TACTIC_DESCRIPTIONS = {
    "slow_scan":           "Conducting slow network scan",
    "ping_sweep":          "Running ping sweep across subnet",
    "passive_listen":      "Passively intercepting traffic",
    "port_probe":          "Probing open ports",
    "service_fingerprint": "Fingerprinting running services",
    "vuln_test":           "Testing for known vulnerabilities",
    "ddos_burst":          "Launching DDoS burst attack",
    "brute_force":         "Brute forcing credentials",
    "payload_inject":      "Injecting malicious payload",
    "privilege_escalate":  "Attempting privilege escalation",
    "lateral_move":        "Moving laterally through network",
    "data_exfil":          "Exfiltrating sensitive data",
    "low_slow":            "Low-and-slow evasion pattern",
    "encrypted_tunnel":    "Using encrypted covert channel",
    "idle_wait":           "Lying dormant to avoid detection",
    "unknown":             "Unknown activity pattern",
}

ACTION_EXPLANATIONS = {
    ("OBSERVE",  "RECON"):    "Gathering intelligence on attacker behavior",
    ("OBSERVE",  "PROBE"):    "Monitoring probe attempts silently",
    ("DECEIVE",  "PROBE"):    "Misleading attacker into false progress",
    ("DECEIVE",  "EXPLOIT"):  "Redirecting attacker to decoy environment",
    ("DECEIVE",  "RECON"):    "Feeding attacker false system information",
    ("BLOCK",    "ESCALATE"): "Stopping escalation attempt immediately",
    ("BLOCK",    "EXPLOIT"):  "Blocking active exploitation attempt",
    ("THROTTLE", "ESCALATE"): "Slowing escalation to limit damage",
    ("THROTTLE", "PROBE"):    "Rate-limiting suspicious probe traffic",
    ("ALLOW",    "RECON"):    "Allowing reconnaissance — low risk phase",
}


class SimulationEngine:
    def __init__(self):
        self.env = MultiAttackerEnvironment(num_attackers=3)
        self.trackers = [BehaviorTracker(window_size=10) for _ in range(3)]
        self.cost_model = DefenseCostModel()

        self.agent = DQNAgent(state_dim=9, actions=ACTIONS)
        model_path = os.path.join(
            os.path.dirname(__file__), '..', 'models', 'dqn_firewall.pt'
        )
        self.agent.load(model_path)

        self.step = 0
        self.total_rewards = []
        self.action_totals = {a: 0 for a in ACTIONS}
        self.event_log = []

        # Per-attacker history for charts
        self.rate_history = [[] for _ in range(3)]
        self.reward_history = []

    def get_explanation(self, action, phase):
        return ACTION_EXPLANATIONS.get(
            (action, phase),
            f"Applying {action.lower()} response to {phase.lower()} activity"
        )

    def get_threat_level(self, phases):
        score = 0
        weights = {
            "RECON": 1, "PROBE": 2,
            "EXPLOIT": 4, "ESCALATE": 5, "STEALTH": 1
        }
        for p in phases:
            score += weights.get(p, 0)
        max_score = 5 * len(phases)
        return round((score / max_score) * 100)

    def step_simulation(self):
        self.step += 1
        states = []

        for i, attacker in enumerate(self.env.attackers):
            activity = attacker.generate_activity()
            self.trackers[i].update(activity["rate"])
            behavioral = self.trackers[i].get_features()
            phase_enc = np.array(
                PHASE_ENCODING[attacker.phase], dtype=np.float32
            )
            state = np.concatenate([behavioral, phase_enc])
            states.append((state, activity, attacker))

        attackers_data = []
        total_reward = 0

        for i, (state, activity, attacker) in enumerate(states):
            action_idx = self.agent.act(state)
            action = ACTIONS[action_idx]

            attacker.update_strategy(action)

            self.action_totals[action] += 1
            self.rate_history[i].append(activity["rate"])
            if len(self.rate_history[i]) > 50:
                self.rate_history[i].pop(0)

            cost = self.cost_model.get_cost(action)
            reward = self._reward(action_idx, attacker.phase) - cost * 0.5
            total_reward += reward

            attackers_data.append({
                "id": i,
                "name": f"Attacker {chr(65+i)}",
                "phase": attacker.phase,
                "phase_color": PHASE_COLORS[attacker.phase],
                "tactic": activity.get("type", "unknown"),
                "tactic_desc": TACTIC_DESCRIPTIONS.get(
                    activity.get("type", "unknown"), "Unknown activity"
                ),
                "rate": int(activity["rate"]),
                "failed_logins": activity.get("failed_logins", 0),
                "confidence": round(attacker.confidence * 100),
                "frustration": round(attacker.frustration * 100),
                "action": action,
                "action_color": ACTION_COLORS[action],
                "explanation": self.get_explanation(action, attacker.phase),
                "deep_explanation": self.generate_explanation(attacker, action, reward),  # NEW
            })

            # Add to event log
            self.event_log.insert(0, {
                "step": self.step,
                "attacker": f"Attacker {chr(65+i)}",
                "phase": attacker.phase,
                "tactic": activity.get("type", "unknown"),
                "action": action,
                "action_color": ACTION_COLORS[action],
                "phase_color": PHASE_COLORS[attacker.phase],
                "reward": round(reward, 2),
            })

        # Keep log at max 100 entries
        self.event_log = self.event_log[:100]

        avg_reward = total_reward / 3
        self.total_rewards.append(round(avg_reward, 2))
        self.reward_history.append(round(avg_reward, 2))
        if len(self.reward_history) > 80:
            self.reward_history.pop(0)

        phases = [a["phase"] for a in attackers_data]
        threat_level = self.get_threat_level(phases)

        return {
            "step": self.step,
            "attackers": attackers_data,
            "threat_level": threat_level,
            "avg_reward": round(avg_reward, 2),
            "reward_history": self.reward_history,
            "action_totals": self.action_totals.copy(),
            "event_log": self.event_log[:20],
            "rate_history": self.rate_history,
        }

    def inject_attack(self, attacker_id, attack_type):
        """Force an attacker into a specific attack scenario"""
        if attacker_id == "all":
            targets = self.env.attackers
        else:
            targets = [self.env.attackers[int(attacker_id)]]

        for attacker in targets:
            if attack_type == "ddos":
                attacker.phase = "ESCALATE"
                attacker.confidence = 0.95
                attacker.frustration = 0.0
                attacker.current_tactic = "ddos_burst"

            elif attack_type == "brute_force":
                attacker.phase = "PROBE"
                attacker.confidence = 0.65
                attacker.frustration = 0.0
                attacker.current_tactic = "brute_force"

            elif attack_type == "stealth":
                attacker.phase = "RECON"
                attacker.confidence = 0.3
                attacker.frustration = 0.0
                attacker.current_tactic = "passive_listen"

            elif attack_type == "coordinated":
                # All attackers escalate simultaneously
                attacker.phase = "ESCALATE"
                attacker.confidence = 0.9
                attacker.frustration = 0.0
                attacker.current_tactic = "lateral_move"

            elif attack_type == "exfil":
                attacker.phase = "ESCALATE"
                attacker.confidence = 0.85
                attacker.frustration = 0.0
                attacker.current_tactic = "data_exfil"

            elif attack_type == "reset":
                attacker.phase = "RECON"
                attacker.confidence = 0.3
                attacker.frustration = 0.0
                attacker.current_tactic = "slow_scan"

        return {"status": "injected", "type": attack_type}

    def _reward(self, action, phase):
        decision = ACTIONS[action]
        if decision == "BLOCK" and phase == "ESCALATE": return 18
        if decision == "BLOCK" and phase == "EXPLOIT":  return 12
        if decision == "BLOCK" and phase == "RECON":    return -4
        if decision == "BLOCK" and phase == "PROBE":    return -2
        if decision == "DECEIVE" and phase == "PROBE":  return 18
        if decision == "DECEIVE" and phase == "EXPLOIT":return 10
        if decision == "DECEIVE" and phase == "RECON":  return 6
        if decision == "OBSERVE" and phase == "RECON":  return 12
        if decision == "OBSERVE" and phase == "PROBE":  return 10
        if decision == "THROTTLE" and phase == "ESCALATE": return 8
        if decision == "THROTTLE":                      return 5
        if decision == "ALLOW" and phase in ["EXPLOIT", "ESCALATE"]: return -25
        return 1
    
    def generate_explanation(self, attacker, action, reward):
        phase = attacker.phase
        conf = round(attacker.confidence * 100)
        frus = round(attacker.frustration * 100)

        explanations = {
            ("BLOCK", "ESCALATE"): {
                "why": f"Attacker is in full ESCALATE mode with {conf}% confidence. Immediate blocking is critical to prevent system compromise. High packet rate indicates active exploitation attempt.",
                "risk": "ALLOW during ESCALATE would result in -25 reward penalty — worst case scenario.",
                "strategy": "Emergency containment — stop escalation immediately"
            },
            ("BLOCK", "EXPLOIT"): {
                "why": f"Active exploitation detected. Attacker confidence at {conf}%. Blocking cuts off the attack vector before damage occurs.",
                "risk": "Delayed response allows payload injection and credential theft.",
                "strategy": "Active threat neutralization"
            },
            ("DECEIVE", "PROBE"): {
                "why": f"Attacker is probing with {conf}% confidence. Deception feeds false system information, wasting attacker resources and gathering intelligence without revealing our detection capability.",
                "risk": "Blocking during PROBE would alert attacker — they would switch tactics.",
                "strategy": "Honeypot redirection — intelligence-first containment"
            },
            ("DECEIVE", "EXPLOIT"): {
                "why": f"Exploitation attempt detected. Deception redirects attacker to decoy environment, protecting real assets while monitoring their techniques.",
                "risk": "Direct block would terminate intelligence gathering opportunity.",
                "strategy": "Active deception — protect real assets via misdirection"
            },
            ("OBSERVE", "RECON"): {
                "why": f"Attacker is in early RECON phase with only {conf}% confidence. Silent observation gathers behavioral intelligence without alerting the attacker.",
                "risk": "Blocking too early reveals detection capability and pushes attacker to stealth mode.",
                "strategy": "Passive intelligence gathering — let attacker reveal their tactics"
            },
            ("OBSERVE", "PROBE"): {
                "why": f"Probe attempts detected. Observing allows us to map attacker's target profile before intervening strategically.",
                "risk": "Premature blocking forces attacker underground into stealth mode.",
                "strategy": "Tactical patience — build complete threat profile first"
            },
            ("THROTTLE", "ESCALATE"): {
                "why": f"Escalation detected but full blocking would disrupt legitimate traffic. Throttling slows attacker's packet rate while maintaining service availability.",
                "risk": "Full block would cause service disruption costing 9 operational units.",
                "strategy": "Controlled degradation — limit damage without full service loss"
            },
            ("ALLOW", "RECON"): {
                "why": f"Early reconnaissance with low confidence ({conf}%). Allowing continues normal operations — threat level too low to justify intervention cost.",
                "risk": "Over-reacting to RECON wastes defensive resources.",
                "strategy": "Minimal intervention — conserve defensive resources"
            },
        }

        key = (action, phase)
        if key in explanations:
            exp = explanations[key]
        else:
            exp = {
                "why": f"Attacker in {phase} phase with {conf}% confidence and {frus}% frustration. Standard {action.lower()} response applied based on behavioral pattern analysis.",
                "risk": "Suboptimal action selection may reduce reward efficiency.",
                "strategy": f"Default {action.lower()} policy"
            }

        return {
            "action": action,
            "phase": phase,
            "confidence": conf,
            "frustration": frus,
            "why": exp["why"],
            "risk": exp["risk"],
            "strategy": exp["strategy"],
            "reward": round(reward, 2)
        }