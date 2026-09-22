# algorithms/reinforcement_learning/fjsp_env.py

import numpy as np

from core.schedule import Schedule, ScheduleEntry


class FJSPEnvironment:

    def __init__(self, machines, jobs):

        self.machines = machines
        self.jobs = jobs

        self.machine_ids = [
            machine.machine_id
            for machine in machines
        ]

        self.job_ids = [
            job.job_id
            for job in jobs
        ]

        self.job_dict = {
            job.job_id: job
            for job in jobs
        }


        # ============================================================
        # 전체 가능한 Action 생성
        # ============================================================

        # Action 하나:
        #
        # (job_id, operation_index, machine_id)
        #
        # 예:
        # ("J1", 0, "M1")
        #
        # = J1의 첫 번째 Operation을 M1에 할당

        self.actions = []

        for job in jobs:

            for op_index, operation in enumerate(
                job.operations
            ):

                for machine_id in (
                    operation.get_available_machines()
                ):

                    self.actions.append(
                        (
                            job.job_id,
                            op_index,
                            machine_id
                        )
                    )


        self.action_size = len(
            self.actions
        )


        # 전체 Operation 개수
        self.total_operations = sum(
            len(job.operations)
            for job in jobs
        )


        self.reset()


    # ============================================================
    # Environment 초기화
    # ============================================================

    def reset(self):

        # 각 Machine이 언제부터 사용 가능한가?
        self.machine_available_time = {
            machine.machine_id: 0
            for machine in self.machines
        }


        # 각 Job의 이전 Operation 종료시간
        self.job_available_time = {
            job.job_id: 0
            for job in self.jobs
        }


        # 각 Job에서 다음으로 처리할 Operation
        self.next_operation_index = {
            job.job_id: 0
            for job in self.jobs
        }


        # 완료 Operation 개수
        self.scheduled_count = 0


        # 현재 스케줄
        self.schedule = Schedule()


        # 현재 Makespan
        self.current_makespan = 0


        return self.get_state()


    # ============================================================
    # 현재 가능한 Action
    # ============================================================

    def get_valid_actions(self):

        valid_actions = []


        for action_index, action in enumerate(
            self.actions
        ):

            job_id, op_index, machine_id = action


            # 현재 해당 Job이 처리해야 하는 Operation인가?
            if (
                self.next_operation_index[job_id]
                == op_index
            ):

                valid_actions.append(
                    action_index
                )


        return valid_actions


    # ============================================================
    # Action Mask
    # ============================================================

    def get_action_mask(self):

        mask = np.zeros(
            self.action_size,
            dtype=np.float32
        )


        for action_index in self.get_valid_actions():

            mask[action_index] = 1.0


        return mask


    # ============================================================
    # State 생성 - DQN용 벡터 상태
    # ============================================================

    def get_state(self):

        state = []


        # ------------------------------------------------------------
        # Job 진행 상태
        # ------------------------------------------------------------

        for job in self.jobs:

            total_ops = len(
                job.operations
            )

            current_op = (
                self.next_operation_index[
                    job.job_id
                ]
            )

            # Job 진행률
            progress = (
                current_op / total_ops
            )

            state.append(
                progress
            )


        # ------------------------------------------------------------
        # Job Ready Time
        # ------------------------------------------------------------

        scale = max(
            1.0,
            float(
                max(
                    [self.current_makespan]
                    + list(
                        self.job_available_time.values()
                    )
                    + list(
                        self.machine_available_time.values()
                    )
                )
            )
        )


        for job in self.jobs:

            state.append(
                self.job_available_time[
                    job.job_id
                ] / scale
            )


        # ------------------------------------------------------------
        # Machine Ready Time
        # ------------------------------------------------------------

        for machine in self.machines:

            state.append(
                self.machine_available_time[
                    machine.machine_id
                ] / scale
            )


        return np.array(
            state,
            dtype=np.float32
        )


    # ============================================================
    # Action 실행
    # ============================================================

    def step(self, action_index):

        valid_actions = (
            self.get_valid_actions()
        )


        # 잘못된 Action
        if action_index not in valid_actions:

            return (
                self.get_state(),
                -10.0,
                False,
                {"invalid_action": True}
            )


        job_id, op_index, machine_id = (
            self.actions[
                action_index
            ]
        )


        job = self.job_dict[
            job_id
        ]

        operation = job.operations[
            op_index
        ]


        processing_time = (
            operation.get_processing_time(
                machine_id
            )
        )


        # ============================================================
        # 작업 시작시간
        # ============================================================

        start_time = max(
            self.job_available_time[
                job_id
            ],
            self.machine_available_time[
                machine_id
            ]
        )


        end_time = (
            start_time
            + processing_time
        )


        # ============================================================
        # Reward 계산 전 기존 Makespan 저장
        # ============================================================

        old_makespan = (
            self.current_makespan
        )


        # ============================================================
        # Schedule에 등록
        # ============================================================

        entry = ScheduleEntry(
            job_id=job_id,
            operation_id=operation.operation_id,
            machine_id=machine_id,
            start_time=start_time,
            end_time=end_time
        )


        self.schedule.add_entry(
            entry
        )


        # ============================================================
        # 상태 갱신
        # ============================================================

        self.machine_available_time[
            machine_id
        ] = end_time


        self.job_available_time[
            job_id
        ] = end_time


        self.next_operation_index[
            job_id
        ] += 1


        self.scheduled_count += 1


        self.current_makespan = max(
            self.current_makespan,
            end_time
        )


        # ============================================================
        # Reward
        # ============================================================

        # Makespan 증가량만큼 음수 보상.
        #
        # 기존 makespan = 5
        # 새 makespan = 8
        #
        # reward = -(8-5)
        #        = -3
        #
        # Makespan을 적게 증가시키는 Action을 선호.

        reward = -(
            self.current_makespan
            - old_makespan
        )


        # ============================================================
        # 종료 여부
        # ============================================================

        done = (
            self.scheduled_count
            == self.total_operations
        )


        return (
            self.get_state(),
            reward,
            done,
            {
                "makespan":
                    self.current_makespan
            }
        )