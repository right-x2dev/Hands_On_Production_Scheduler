# algorithms/reinforcement_learning/gnn_ppo.py

import numpy as np

import torch
import torch.nn as nn
import torch.optim as optim

from torch.distributions import Categorical

from algorithms.reinforcement_learning.fjsp_env import (
    FJSPEnvironment
)


# ============================================================
# Simple GNN Layer
# ============================================================

class GraphLayer(nn.Module):

    def __init__(
        self,
        input_dim,
        output_dim
    ):

        super().__init__()


        self.self_linear = nn.Linear(
            input_dim,
            output_dim
        )


        self.neighbor_linear = nn.Linear(
            input_dim,
            output_dim
        )


    def forward(
        self,
        x,
        adjacency
    ):

        # x
        # [num_nodes, feature_dim]

        # adjacency
        # [num_nodes, num_nodes]


        degree = adjacency.sum(
            dim=1,
            keepdim=True
        ).clamp(
            min=1
        )


        neighbor_feature = (
            adjacency @ x
        ) / degree


        output = (
            self.self_linear(x)
            +
            self.neighbor_linear(
                neighbor_feature
            )
        )


        return torch.relu(
            output
        )


# ============================================================
# GNN Actor-Critic Network
# ============================================================

class GNNActorCritic(nn.Module):

    def __init__(
        self,
        node_feature_dim=6,
        hidden_dim=128
    ):

        super().__init__()


        self.gnn1 = GraphLayer(
            node_feature_dim,
            hidden_dim
        )


        self.gnn2 = GraphLayer(
            hidden_dim,
            hidden_dim
        )


        # ------------------------------------------------------------
        # Actor
        # ------------------------------------------------------------

        # Operation embedding
        # +
        # Machine embedding
        # +
        # Global graph embedding

        self.actor = nn.Sequential(

            nn.Linear(
                hidden_dim * 3,
                128
            ),

            nn.ReLU(),

            nn.Linear(
                128,
                1
            )
        )


        # ------------------------------------------------------------
        # Critic
        # ------------------------------------------------------------

        self.critic = nn.Sequential(

            nn.Linear(
                hidden_dim,
                128
            ),

            nn.ReLU(),

            nn.Linear(
                128,
                1
            )
        )


    # ============================================================
    # Graph Encoding
    # ============================================================

    def encode(
        self,
        node_features,
        adjacency
    ):

        h = self.gnn1(
            node_features,
            adjacency
        )


        h = self.gnn2(
            h,
            adjacency
        )


        return h


    # ============================================================
    # Actor / Critic
    # ============================================================

    def forward(
        self,
        node_features,
        adjacency,
        action_pairs
    ):

        h = self.encode(
            node_features,
            adjacency
        )


        # 전체 Graph representation
        global_embedding = h.mean(
            dim=0
        )


        logits = []


        for (
            operation_node,
            machine_node
        ) in action_pairs:

            action_embedding = torch.cat(
                [
                    h[operation_node],
                    h[machine_node],
                    global_embedding
                ]
            )


            logit = self.actor(
                action_embedding
            )


            logits.append(
                logit
            )


        logits = torch.stack(
            logits
        ).squeeze(-1)


        value = self.critic(
            global_embedding
        ).squeeze(-1)


        return logits, value


# ============================================================
# GNN + PPO Scheduler
# ============================================================

class GNNPPOScheduler:

    def __init__(
        self,
        episodes=1000,
        gamma=0.99,
        learning_rate=0.0003,
        clip_epsilon=0.2,
        update_epochs=5
    ):

        self.episodes = episodes
        self.gamma = gamma

        self.learning_rate = (
            learning_rate
        )

        self.clip_epsilon = (
            clip_epsilon
        )

        self.update_epochs = (
            update_epochs
        )


    # ============================================================
    # 전체 학습
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


        graph_info = (
            self._build_static_graph(
                env
            )
        )


        (
            operation_nodes,
            machine_nodes,
            adjacency,
            action_pairs
        ) = graph_info


        model = GNNActorCritic()


        optimizer = optim.Adam(
            model.parameters(),
            lr=self.learning_rate
        )


        # ============================================================
        # Episode 반복
        # ============================================================

        for episode in range(
            self.episodes
        ):

            env.reset()


            trajectory = []


            done = False


            while not done:

                # ====================================================
                # Graph State 생성
                # ====================================================

                node_features = (
                    self._build_node_features(
                        env,
                        operation_nodes,
                        machine_nodes
                    )
                )


                logits, value = model(
                    node_features,
                    adjacency,
                    action_pairs
                )


                # ====================================================
                # Action Mask
                # ====================================================

                valid_mask = torch.tensor(
                    env.get_action_mask(),
                    dtype=torch.bool
                )


                masked_logits = (
                    logits.clone()
                )


                masked_logits[
                    ~valid_mask
                ] = -1e9


                distribution = Categorical(
                    logits=masked_logits
                )


                action = distribution.sample()


                log_prob = (
                    distribution.log_prob(
                        action
                    )
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
                    int(
                        action.item()
                    )
                )


                trajectory.append(
                    {
                        "features":
                            node_features.detach(),

                        "action":
                            action.detach(),

                        "log_prob":
                            log_prob.detach(),

                        "value":
                            value.detach(),

                        "reward":
                            reward,

                        "mask":
                            valid_mask
                    }
                )


            # ========================================================
            # PPO Update
            # ========================================================

            self._ppo_update(
                model,
                optimizer,
                adjacency,
                action_pairs,
                trajectory
            )


        # ============================================================
        # 학습 완료 후 Greedy Scheduling
        # ============================================================

        return self._evaluate(
            env,
            model,
            operation_nodes,
            machine_nodes,
            adjacency,
            action_pairs
        )


    # ============================================================
    # Graph 기본 구조 생성
    # ============================================================

    def _build_static_graph(
        self,
        env
    ):

        operation_nodes = {}

        machine_nodes = {}


        node_index = 0


        # ============================================================
        # Operation Nodes
        # ============================================================

        for job in env.jobs:

            for op_index, operation in enumerate(
                job.operations
            ):

                operation_nodes[
                    (
                        job.job_id,
                        op_index
                    )
                ] = node_index

                node_index += 1


        # ============================================================
        # Machine Nodes
        # ============================================================

        for machine in env.machines:

            machine_nodes[
                machine.machine_id
            ] = node_index

            node_index += 1


        num_nodes = node_index


        adjacency = torch.zeros(
            (
                num_nodes,
                num_nodes
            ),
            dtype=torch.float32
        )


        # ============================================================
        # Precedence Edge
        # ============================================================

        for job in env.jobs:

            for op_index in range(
                len(job.operations) - 1
            ):

                a = operation_nodes[
                    (
                        job.job_id,
                        op_index
                    )
                ]

                b = operation_nodes[
                    (
                        job.job_id,
                        op_index + 1
                    )
                ]


                adjacency[a, b] = 1
                adjacency[b, a] = 1


        # ============================================================
        # Operation - Machine Eligibility Edge
        # ============================================================

        for job in env.jobs:

            for op_index, operation in enumerate(
                job.operations
            ):

                op_node = operation_nodes[
                    (
                        job.job_id,
                        op_index
                    )
                ]


                for machine_id in (
                    operation.get_available_machines()
                ):

                    machine_node = (
                        machine_nodes[
                            machine_id
                        ]
                    )


                    adjacency[
                        op_node,
                        machine_node
                    ] = 1


                    adjacency[
                        machine_node,
                        op_node
                    ] = 1


        # ============================================================
        # Action → (Operation Node, Machine Node)
        # ============================================================

        action_pairs = []


        for (
            job_id,
            op_index,
            machine_id
        ) in env.actions:

            action_pairs.append(
                (
                    operation_nodes[
                        (
                            job_id,
                            op_index
                        )
                    ],
                    machine_nodes[
                        machine_id
                    ]
                )
            )


        return (
            operation_nodes,
            machine_nodes,
            adjacency,
            action_pairs
        )


    # ============================================================
    # 현재 Graph Node Feature 생성
    # ============================================================

    def _build_node_features(
        self,
        env,
        operation_nodes,
        machine_nodes
    ):

        num_nodes = (
            len(operation_nodes)
            +
            len(machine_nodes)
        )


        # Node feature:
        #
        # [0] Operation 여부
        # [1] Machine 여부
        # [2] 현재 실행 가능 여부
        # [3] 완료 여부
        # [4] Ready Time
        # [5] Processing Time 관련 feature

        features = torch.zeros(
            (
                num_nodes,
                6
            ),
            dtype=torch.float32
        )


        scale = max(
            1.0,
            float(
                env.current_makespan
            )
        )


        # ============================================================
        # Operation Features
        # ============================================================

        for job in env.jobs:

            for op_index, operation in enumerate(
                job.operations
            ):

                node = operation_nodes[
                    (
                        job.job_id,
                        op_index
                    )
                ]


                # Operation node
                features[
                    node,
                    0
                ] = 1.0


                current_op = (
                    env.next_operation_index[
                        job.job_id
                    ]
                )


                # 현재 실행 가능 Operation
                if op_index == current_op:

                    features[
                        node,
                        2
                    ] = 1.0


                # 이미 완료
                if op_index < current_op:

                    features[
                        node,
                        3
                    ] = 1.0


                features[
                    node,
                    4
                ] = (
                    env.job_available_time[
                        job.job_id
                    ]
                    / scale
                )


                min_processing_time = min(
                    operation.processing_times.values()
                )


                features[
                    node,
                    5
                ] = (
                    min_processing_time
                    / scale
                )


        # ============================================================
        # Machine Features
        # ============================================================

        for machine in env.machines:

            node = machine_nodes[
                machine.machine_id
            ]


            # Machine node
            features[
                node,
                1
            ] = 1.0


            features[
                node,
                4
            ] = (
                env.machine_available_time[
                    machine.machine_id
                ]
                / scale
            )


        return features


    # ============================================================
    # PPO Update
    # ============================================================

    def _ppo_update(
        self,
        model,
        optimizer,
        adjacency,
        action_pairs,
        trajectory
    ):

        # ============================================================
        # Return 계산
        # ============================================================

        returns = []

        discounted_return = 0


        for step in reversed(
            trajectory
        ):

            discounted_return = (
                step["reward"]
                +
                self.gamma
                * discounted_return
            )


            returns.insert(
                0,
                discounted_return
            )


        returns = torch.tensor(
            returns,
            dtype=torch.float32
        )


        old_log_probs = torch.stack(
            [
                step["log_prob"]
                for step in trajectory
            ]
        )


        old_values = torch.stack(
            [
                step["value"]
                for step in trajectory
            ]
        )


        # Advantage
        advantages = (
            returns
            - old_values
        )


        # Advantage normalization
        if len(advantages) > 1:

            advantages = (
                advantages
                - advantages.mean()
            ) / (
                advantages.std()
                + 1e-8
            )


        # ============================================================
        # PPO 여러 Epoch Update
        # ============================================================

        for _ in range(
            self.update_epochs
        ):

            actor_losses = []
            critic_losses = []


            for index, step in enumerate(
                trajectory
            ):

                logits, value = model(
                    step["features"],
                    adjacency,
                    action_pairs
                )


                masked_logits = (
                    logits.clone()
                )


                masked_logits[
                    ~step["mask"]
                ] = -1e9


                distribution = (
                    Categorical(
                        logits=masked_logits
                    )
                )


                new_log_prob = (
                    distribution.log_prob(
                        step["action"]
                    )
                )


                ratio = torch.exp(
                    new_log_prob
                    - old_log_probs[index]
                )


                advantage = (
                    advantages[index]
                )


                # PPO clipping
                surrogate1 = (
                    ratio
                    * advantage
                )


                surrogate2 = (
                    torch.clamp(
                        ratio,
                        1.0
                        - self.clip_epsilon,
                        1.0
                        + self.clip_epsilon
                    )
                    * advantage
                )


                actor_loss = -torch.min(
                    surrogate1,
                    surrogate2
                )


                critic_loss = (
                    value
                    - returns[index]
                ) ** 2


                actor_losses.append(
                    actor_loss
                )

                critic_losses.append(
                    critic_loss
                )


            total_loss = (

                torch.stack(
                    actor_losses
                ).mean()

                +

                0.5
                * torch.stack(
                    critic_losses
                ).mean()
            )


            optimizer.zero_grad()

            total_loss.backward()

            optimizer.step()


    # ============================================================
    # 학습된 Policy로 Schedule 생성
    # ============================================================

    def _evaluate(
        self,
        env,
        model,
        operation_nodes,
        machine_nodes,
        adjacency,
        action_pairs
    ):

        env.reset()

        done = False


        while not done:

            node_features = (
                self._build_node_features(
                    env,
                    operation_nodes,
                    machine_nodes
                )
            )


            with torch.no_grad():

                logits, value = model(
                    node_features,
                    adjacency,
                    action_pairs
                )


            valid_mask = torch.tensor(
                env.get_action_mask(),
                dtype=torch.bool
            )


            logits[
                ~valid_mask
            ] = -1e9


            action = int(
                torch.argmax(
                    logits
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
    
    
    
