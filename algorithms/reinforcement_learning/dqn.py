#고정 길이 벡터 state + 이산 action
# algorithms/reinforcement_learning/dqn.py

import random
import collections

import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim

from algorithms.reinforcement_learning.fjsp_env import (
    FJSPEnvironment
)


# ============================================================
# Replay Buffer
# ============================================================

class ReplayBuffer:

    def __init__(
        self,
        capacity=50000
    ):

        self.buffer = collections.deque(
            maxlen=capacity
        )


    def put(self, transition):

        self.buffer.append(
            transition
        )


    def sample(self, batch_size):

        return random.sample(
            self.buffer,
            batch_size
        )


    def __len__(self):

        return len(
            self.buffer
        )


# ============================================================
# DQN Network
# ============================================================

class QNetwork(nn.Module):

    def __init__(
        self,
        state_size,
        action_size
    ):

        super().__init__()


        self.network = nn.Sequential(

            nn.Linear(
                state_size,
                128
            ),

            nn.ReLU(),

            nn.Linear(
                128,
                128
            ),

            nn.ReLU(),

            nn.Linear(
                128,
                action_size
            )
        )


    def forward(self, x):

        return self.network(
            x
        )


# ============================================================
# DQN Scheduler
# ============================================================

class DQNScheduler:

    def __init__(
        self,
        episodes=1000,
        gamma=0.99,
        learning_rate=0.001,
        batch_size=64,
        epsilon_start=1.0,
        epsilon_end=0.05,
        epsilon_decay=0.995,
        target_update_interval=20
    ):

        self.episodes = episodes
        self.gamma = gamma
        self.learning_rate = learning_rate
        self.batch_size = batch_size

        self.epsilon_start = (
            epsilon_start
        )

        self.epsilon_end = (
            epsilon_end
        )

        self.epsilon_decay = (
            epsilon_decay
        )

        self.target_update_interval = (
            target_update_interval
        )


    # ============================================================
    # 전체 DQN 학습
    # ============================================================

    def solve(
        self,
        machines,
        jobs
    ):

        env = FJSPEnvironment(
            machines,
            jobs
        )


        initial_state = env.reset()

        state_size = len(
            initial_state
        )

        action_size = (
            env.action_size
        )


        # ============================================================
        # Main Network / Target Network
        # ============================================================

        q_network = QNetwork(
            state_size,
            action_size
        )


        target_network = QNetwork(
            state_size,
            action_size
        )


        target_network.load_state_dict(
            q_network.state_dict()
        )


        optimizer = optim.Adam(
            q_network.parameters(),
            lr=self.learning_rate
        )


        replay_buffer = (
            ReplayBuffer()
        )


        epsilon = (
            self.epsilon_start
        )


        # ============================================================
        # Episode 반복
        # ============================================================

        for episode in range(
            self.episodes
        ):

            state = env.reset()

            done = False


            while not done:

                valid_actions = (
                    env.get_valid_actions()
                )


                # ====================================================
                # Epsilon-Greedy
                # ====================================================

                if random.random() < epsilon:

                    action = random.choice(
                        valid_actions
                    )

                else:

                    state_tensor = torch.tensor(
                        state,
                        dtype=torch.float32
                    ).unsqueeze(0)


                    with torch.no_grad():

                        q_values = q_network(
                            state_tensor
                        )[0]


                    # 유효하지 않은 Action은 선택하지 못하도록
                    # -무한대로 Mask 처리.

                    masked_q = torch.full_like(
                        q_values,
                        float("-inf")
                    )


                    masked_q[
                        valid_actions
                    ] = q_values[
                        valid_actions
                    ]


                    action = int(
                        torch.argmax(
                            masked_q
                        ).item()
                    )


                # ====================================================
                # Environment Step
                # ====================================================

                (
                    next_state,
                    reward,
                    done,
                    info
                ) = env.step(
                    action
                )


                next_mask = (
                    env.get_action_mask()
                    if not done
                    else np.zeros(
                        action_size,
                        dtype=np.float32
                    )
                )


                replay_buffer.put(
                    (
                        state,
                        action,
                        reward,
                        next_state,
                        done,
                        next_mask
                    )
                )


                state = next_state


                # ====================================================
                # Network 학습
                # ====================================================

                if (
                    len(replay_buffer)
                    >= self.batch_size
                ):

                    self._train(
                        q_network,
                        target_network,
                        optimizer,
                        replay_buffer
                    )


            # ========================================================
            # Epsilon 감소
            # ========================================================

            epsilon = max(
                self.epsilon_end,
                epsilon
                * self.epsilon_decay
            )


            # ========================================================
            # Target Network 갱신
            # ========================================================

            if (
                episode
                % self.target_update_interval
                == 0
            ):

                target_network.load_state_dict(
                    q_network.state_dict()
                )


        # ============================================================
        # 학습 완료 후 Greedy Scheduling
        # ============================================================

        schedule = self._evaluate(
            env,
            q_network
        )


        return schedule


    # ============================================================
    # DQN Training
    # ============================================================

    def _train(
        self,
        q_network,
        target_network,
        optimizer,
        replay_buffer
    ):

        batch = replay_buffer.sample(
            self.batch_size
        )


        (
            states,
            actions,
            rewards,
            next_states,
            dones,
            next_masks
        ) = zip(
            *batch
        )


        states = torch.tensor(
            np.array(states),
            dtype=torch.float32
        )


        actions = torch.tensor(
            actions,
            dtype=torch.long
        )


        rewards = torch.tensor(
            rewards,
            dtype=torch.float32
        )


        next_states = torch.tensor(
            np.array(next_states),
            dtype=torch.float32
        )


        dones = torch.tensor(
            dones,
            dtype=torch.float32
        )


        next_masks = torch.tensor(
            np.array(next_masks),
            dtype=torch.bool
        )


        # ============================================================
        # 현재 Q(s,a)
        # ============================================================

        q_values = q_network(
            states
        )


        current_q = q_values.gather(
            1,
            actions.unsqueeze(1)
        ).squeeze(1)


        # ============================================================
        # Target Q
        # ============================================================

        with torch.no_grad():

            next_q = target_network(
                next_states
            )


            next_q[
                ~next_masks
            ] = float("-inf")


            next_max_q = torch.max(
                next_q,
                dim=1
            ).values


            # done 상태는 next Q 사용하지 않음
            next_max_q = torch.where(
                dones.bool(),
                torch.zeros_like(
                    next_max_q
                ),
                next_max_q
            )


            target_q = (
                rewards
                +
                self.gamma
                * next_max_q
                * (1 - dones)
            )


        # ============================================================
        # Loss
        # ============================================================

        loss = nn.functional.mse_loss(
            current_q,
            target_q
        )


        optimizer.zero_grad()

        loss.backward()

        optimizer.step()


    # ============================================================
    # 학습된 DQN으로 실제 Schedule 생성
    # ============================================================

    def _evaluate(
        self,
        env,
        q_network
    ):

        state = env.reset()

        done = False


        while not done:

            valid_actions = (
                env.get_valid_actions()
            )


            state_tensor = torch.tensor(
                state,
                dtype=torch.float32
            ).unsqueeze(0)


            with torch.no_grad():

                q_values = q_network(
                    state_tensor
                )[0]


            masked_q = torch.full_like(
                q_values,
                float("-inf")
            )


            masked_q[
                valid_actions
            ] = q_values[
                valid_actions
            ]


            action = int(
                torch.argmax(
                    masked_q
                ).item()
            )


            (
                state,
                reward,
                done,
                info
            ) = env.step(
                action
            )


        return env.schedule