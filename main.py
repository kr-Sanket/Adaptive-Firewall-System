from agent.dqn_agent import DQNAgent
from agent.replay_buffer import ReplayBuffer
from environment.behavior_tracker import BehaviorTracker
from environment.cost_model import DefenseCostModel
from environment.multi_attacker_env import MultiAttackerEnvironment

import numpy as np

# Strategic defense actions
ACTIONS = ["ALLOW", "BLOCK", "THROTTLE", "OBSERVE", "DECEIVE"]

# Phase one-hot encoding — gives defender awareness of attacker intent
PHASE_ENCODING = {
    "RECON":    [1, 0, 0, 0, 0],
    "PROBE":    [0, 1, 0, 0, 0],
    "EXPLOIT":  [0, 0, 1, 0, 0],
    "ESCALATE": [0, 0, 0, 1, 0],
    "STEALTH":  [0, 0, 0, 0, 1],
}


# -----------------------------
# Strategic Reward Function
# -----------------------------
def reward_function(action, attacker_phase):
    decision = ACTIONS[action]

    # === BLOCK rewards ===
    if decision == "BLOCK" and attacker_phase == "ESCALATE":
        return 18

    if decision == "BLOCK" and attacker_phase == "EXPLOIT":
        return 12

    if decision == "BLOCK" and attacker_phase == "RECON":
        return -4  # too early, lose intelligence

    if decision == "BLOCK" and attacker_phase == "PROBE":
        return -2  # should deceive instead

    # === DECEIVE rewards ===
    if decision == "DECEIVE" and attacker_phase == "PROBE":
        return 18

    if decision == "DECEIVE" and attacker_phase == "EXPLOIT":
        return 10

    if decision == "DECEIVE" and attacker_phase == "RECON":
        return 6

    # === OBSERVE rewards ===
    if decision == "OBSERVE" and attacker_phase == "RECON":
        return 12

    if decision == "OBSERVE" and attacker_phase == "PROBE":
        return 10

    # === THROTTLE ===
    if decision == "THROTTLE" and attacker_phase == "ESCALATE":
        return 8

    if decision == "THROTTLE":
        return 5

    # === ALLOW ===
    if decision == "ALLOW" and attacker_phase in ["EXPLOIT", "ESCALATE"]:
        return -25

    return 1


# -----------------------------
# Training Loop (Multi-Attacker)
# -----------------------------
def train(steps=30000):

    NUM_ATTACKERS = 3

    env = MultiAttackerEnvironment(num_attackers=NUM_ATTACKERS)
    trackers = [BehaviorTracker(window_size=10) for _ in range(NUM_ATTACKERS)]

    # state_dim = 4 behavioral features + 5 phase encoding = 9
    agent = DQNAgent(state_dim=9, actions=ACTIONS)
    buffer = ReplayBuffer()
    cost_model = DefenseCostModel()

    rewards = []
    action_counts = {a: 0 for a in ACTIONS}

    for step in range(steps):

        states = []

        # ---- Build state for each attacker (behavior + phase) ----
        for i, attacker in enumerate(env.attackers):
            activity = attacker.generate_activity()
            trackers[i].update(activity["rate"])

            behavioral_features = trackers[i].get_features()          # shape: (4,)
            phase_features = np.array(
                PHASE_ENCODING[attacker.phase], dtype=np.float32      # shape: (5,)
            )

            state = np.concatenate([behavioral_features, phase_features])  # shape: (9,)
            states.append(state)

        # ---- Defender chooses action per attacker ----
        actions = [agent.act(state) for state in states]
        decisions = [ACTIONS[a] for a in actions]

        # ---- Track action distribution ----
        for a in actions:
            action_counts[ACTIONS[a]] += 1

        # ---- Apply decisions back to attackers ----
        for attacker, decision in zip(env.attackers, decisions):
            attacker.update_strategy(decision)

        # ---- Compute Global Reward ----
        reward = 0
        for action, attacker in zip(actions, env.attackers):
            base_reward = reward_function(action, attacker.phase)
            cost_penalty = cost_model.get_cost(ACTIONS[action])
            reward += base_reward - cost_penalty * 0.5

        reward /= NUM_ATTACKERS  # normalize
        rewards.append(reward)

        # ---- Store Experience Per Attacker ----
        for i, attacker in enumerate(env.attackers):
            next_activity = attacker.generate_activity()
            trackers[i].update(next_activity["rate"])

            next_behavioral = trackers[i].get_features()
            next_phase = np.array(
                PHASE_ENCODING[attacker.phase], dtype=np.float32
            )
            next_state = np.concatenate([next_behavioral, next_phase])

            buffer.push(states[i], actions[i], reward, next_state)

        # ---- Learn From Replay ----
        if len(buffer) > 64:
            batch = buffer.sample(32)
            agent.train_batch(*batch)
            agent.decay_exploration()

        # ---- Logging every 500 steps ----
        if (step + 1) % 500 == 0:
            avg_reward = np.mean(rewards[-500:])
            phases = [atk.phase for atk in env.attackers]

            print(
                f"Step {step+1}, Avg Reward: {avg_reward:.2f}, "
                f"Epsilon: {agent.epsilon:.3f}, "
                f"Phases: {phases}"
            )
            print(f"  Action Distribution: {action_counts}")

            # Reset counts for next 500-step window
            action_counts = {a: 0 for a in ACTIONS}

    return agent, rewards


# -----------------------------
# Main Execution
# -----------------------------
def main():
    print("Training Multi-Adversary Strategic Defense System...\n")

    agent, rewards = train()

    print("\nTraining Finished.")

    agent.save("models/dqn_firewall.pt")
    print("Model saved to models/dqn_firewall.pt")


if __name__ == "__main__":
    main()