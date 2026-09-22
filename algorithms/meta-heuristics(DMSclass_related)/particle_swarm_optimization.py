#ScheduleEntry = 작업 하나의 배정 결과
#Schedule = 여러 배정 결과를 모아놓은 전체 일정
from core.schedule import Schedule, ScheduleEntry

#Makespan 계산
from evaluation.kpi import calculate_makespan

import random


#============================================================
# Particle Swarm Optimization + FJSP
#============================================================

#PSO는 여러 개의 Particle(입자)이 동시에 Solution 공간을 탐색하는
#Population-Based Metaheuristic.
#
#각 Particle은:
#
#1. Position
#2. Velocity
#3. Personal Best(pbest)
#
#를 가지고 있음.
#
#그리고 전체 Particle 중 가장 좋은 Solution을:
#
#Global Best(gbest)
#
#라고 함.
#
#기본 흐름:
#
#1. Particle 여러 개 생성
#2. 각 Particle의 Position을 FJSP Solution으로 변환
#3. Decoder로 Schedule 생성
#4. Makespan 평가
#5. Personal Best 갱신
#6. Global Best 갱신
#7. Velocity 갱신
#8. Position 갱신
#9. 반복
#
#목적함수:
#Makespan 최소화


class ParticleSwarmOptimizationScheduler:

    def __init__(
        self,
        num_particles=30,
        max_iterations=100,
        inertia_weight=0.7,
        cognitive_coefficient=1.5,
        social_coefficient=1.5,
        max_velocity=0.2
    ):

        #Particle 개수
        self.num_particles = num_particles

        #PSO 반복 횟수
        self.max_iterations = max_iterations

        #관성계수 w
        #현재 이동 방향을 얼마나 유지할 것인지
        self.inertia_weight = inertia_weight

        #인지계수 c1
        #자신의 Personal Best 방향을 얼마나 따라갈 것인지
        self.cognitive_coefficient = cognitive_coefficient

        #사회계수 c2
        #전체 Global Best 방향을 얼마나 따라갈 것인지
        self.social_coefficient = social_coefficient

        #Velocity가 지나치게 커지는 것을 방지하기 위한 제한
        self.max_velocity = max_velocity


        #최종 결과 저장
        self.best_solution = None
        self.best_makespan = float("inf")


    #============================================================
    # 전체 PSO 실행
    #============================================================

    def solve(self, machines, jobs):

        #============================================================
        # 1. FJSP의 전체 Operation 수 계산
        #============================================================

        total_operations = sum(
            len(job.operations)
            for job in jobs
        )


        #============================================================
        # 2. Particle Population 생성
        #============================================================

        particles = []

        for _ in range(self.num_particles):

            particle = self._create_particle(
                total_operations
            )

            particles.append(
                particle
            )


        #============================================================
        # Global Best 초기화
        #============================================================

        global_best_os_position = None
        global_best_ms_position = None

        global_best_makespan = float("inf")
        global_best_schedule = None
        global_best_solution = None


        #============================================================
        # 3. PSO 반복
        #============================================================

        for iteration in range(
            self.max_iterations
        ):

            #============================================================
            # 모든 Particle 평가
            #============================================================

            for particle in particles:

                #Particle의 연속 Position을
                #실제 FJSP Solution(OS + MS)으로 변환.
                solution = self._position_to_solution(
                    particle,
                    jobs
                )


                #Solution → 실제 Schedule
                schedule = self._decode(
                    solution,
                    machines,
                    jobs
                )


                #Makespan 계산
                makespan = calculate_makespan(
                    schedule
                )


                #============================================================
                # 4. Personal Best 갱신
                #============================================================

                #현재 Particle이 지금까지 자기 자신이 찾았던
                #가장 좋은 결과보다 더 좋은 경우.

                if makespan < particle["best_makespan"]:

                    particle["best_makespan"] = (
                        makespan
                    )

                    particle["best_os_position"] = (
                        particle["os_position"].copy()
                    )

                    particle["best_ms_position"] = (
                        particle["ms_position"].copy()
                    )


                #============================================================
                # 5. Global Best 갱신
                #============================================================

                #전체 Particle이 지금까지 찾은 결과 중
                #가장 좋은 Makespan보다 현재가 더 좋은 경우.

                if makespan < global_best_makespan:

                    global_best_makespan = (
                        makespan
                    )

                    global_best_os_position = (
                        particle["os_position"].copy()
                    )

                    global_best_ms_position = (
                        particle["ms_position"].copy()
                    )

                    global_best_schedule = schedule

                    global_best_solution = {
                        "os": solution["os"].copy(),
                        "ms": solution["ms"].copy()
                    }


            #============================================================
            # 6. 모든 Particle의 Velocity / Position 갱신
            #============================================================

            for particle in particles:

                self._update_particle(
                    particle,
                    global_best_os_position,
                    global_best_ms_position
                )


        #============================================================
        # 최종 결과 저장
        #============================================================

        self.best_makespan = (
            global_best_makespan
        )

        self.best_solution = (
            global_best_solution
        )

        return global_best_schedule



    #============================================================
    # Particle 생성
    #============================================================

    def _create_particle(
        self,
        total_operations
    ):

        #============================================================
        # OS Position
        #============================================================

        #각 Operation 위치를 표현하는 Random-Key.
        #
        #예:
        #
        #OS Position
        #
        #[0.72, 0.10, 0.84, 0.31, 0.55, 0.20]
        #
        #이 값을 작은 순서대로 정렬해서
        #Operation Sequence를 결정할 것.

        os_position = [
            random.random()
            for _ in range(total_operations)
        ]


        #============================================================
        # MS Position
        #============================================================

        #각 Operation의 Machine 선택을 위한 연속값.
        #
        #예:
        #
        #[0.15, 0.72, 0.40, ...]
        #
        #0~1 값을 Machine 후보 index로 변환.

        ms_position = [
            random.random()
            for _ in range(total_operations)
        ]


        #============================================================
        # OS Velocity
        #============================================================

        os_velocity = [
            random.uniform(
                -self.max_velocity,
                self.max_velocity
            )
            for _ in range(total_operations)
        ]


        #============================================================
        # MS Velocity
        #============================================================

        ms_velocity = [
            random.uniform(
                -self.max_velocity,
                self.max_velocity
            )
            for _ in range(total_operations)
        ]


        return {
            "os_position": os_position,
            "ms_position": ms_position,

            "os_velocity": os_velocity,
            "ms_velocity": ms_velocity,

            #처음에는 아직 Personal Best 없음.
            "best_os_position": os_position.copy(),
            "best_ms_position": ms_position.copy(),

            "best_makespan": float("inf")
        }



    #============================================================
    # Particle Position → FJSP Solution 변환
    #============================================================

    def _position_to_solution(
        self,
        particle,
        jobs
    ):

        #============================================================
        # 기본 Operation Sequence 생성
        #============================================================

        #예:
        #
        #J1 = O11, O12
        #J2 = O21, O22
        #J3 = O31, O32
        #
        #base_os:
        #
        #[J1, J2, J3, J1, J2, J3]

        base_os = []


        max_operations = max(
            len(job.operations)
            for job in jobs
        )


        for op_index in range(
            max_operations
        ):

            for job in jobs:

                if op_index < len(job.operations):

                    base_os.append(
                        job.job_id
                    )


        #============================================================
        # OS Random-Key Decode
        #============================================================

        #예:
        #
        #base_os
        #[J1, J2, J3, J1, J2, J3]
        #
        #position
        #[.72,.10,.84,.31,.55,.20]
        #
        #position값이 작은 순서:
        #
        #index 1 → J2
        #index 5 → J3
        #index 3 → J1
        #index 4 → J2
        #index 0 → J1
        #index 2 → J3
        #
        #따라서:
        #
        #OS =
        #[J2, J3, J1, J2, J1, J3]


        sorted_indices = sorted(
            range(len(base_os)),
            key=lambda i: particle[
                "os_position"
            ][i]
        )


        operation_sequence = [
            base_os[i]
            for i in sorted_indices
        ]


        #============================================================
        # Machine Selection 변환
        #============================================================

        machine_selection = {}


        #MS Position의 몇 번째 값을 사용할지
        position_index = 0


        for job in jobs:

            for op_index, operation in enumerate(
                job.operations
            ):

                available_machines = (
                    operation.get_available_machines()
                )


                #0~1 사이의 연속값
                position_value = particle[
                    "ms_position"
                ][position_index]


                #============================================================
                # 연속값 → Machine index
                #============================================================

                #예:
                #
                #Machine 후보:
                #[M1, M2, M3]
                #
                #position = 0.1
                #→ index 0
                #
                #position = 0.5
                #→ index 1
                #
                #position = 0.9
                #→ index 2

                machine_index = int(
                    position_value
                    * len(available_machines)
                )


                #position이 정확히 1에 가까워져서
                #index가 범위를 넘어가는 경우 방지.
                machine_index = min(
                    machine_index,
                    len(available_machines) - 1
                )


                machine_id = (
                    available_machines[
                        machine_index
                    ]
                )


                machine_selection[
                    (job.job_id, op_index)
                ] = machine_id


                position_index += 1


        return {
            "os": operation_sequence,
            "ms": machine_selection
        }



    #============================================================
    # Solution → 실제 FJSP Schedule 변환
    #============================================================

    def _decode(
        self,
        solution,
        machines,
        jobs
    ):

        schedule = Schedule()


        #============================================================
        # 앞의 SPT / EDD / Tabu / SA / GA와 동일한
        # FJSP 상태 관리
        #============================================================

        #각 Machine이 언제부터 사용 가능한지
        machine_available_time = {
            machine.machine_id: 0
            for machine in machines
        }


        #각 Job의 직전 Operation 종료시간
        job_available_time = {
            job.job_id: 0
            for job in jobs
        }


        #각 Job에서 다음으로 처리해야 할 Operation index
        next_operation_index = {
            job.job_id: 0
            for job in jobs
        }


        #Job ID → 실제 Job 객체
        job_dict = {
            job.job_id: job
            for job in jobs
        }


        #============================================================
        # OS 순서대로 Schedule 생성
        #============================================================

        for job_id in solution["os"]:

            job = job_dict[
                job_id
            ]


            #해당 Job의 다음 Operation
            op_index = (
                next_operation_index[
                    job_id
                ]
            )


            operation = (
                job.operations[
                    op_index
                ]
            )


            #MS에서 Machine 확인
            machine_id = (
                solution["ms"][
                    (job_id, op_index)
                ]
            )


            #Processing Time
            processing_time = (
                operation.get_processing_time(
                    machine_id
                )
            )


            #============================================================
            # 시작시간 계산
            #============================================================

            #1. 이전 Operation이 끝나야 함
            #2. Machine이 비어있어야 함

            start_time = max(
                job_available_time[
                    job_id
                ],
                machine_available_time[
                    machine_id
                ]
            )


            end_time = (
                start_time
                + processing_time
            )


            #============================================================
            # ScheduleEntry 생성
            #============================================================

            entry = ScheduleEntry(
                job_id=job_id,
                operation_id=operation.operation_id,
                machine_id=machine_id,
                start_time=start_time,
                end_time=end_time
            )


            schedule.add_entry(
                entry
            )


            #============================================================
            # 상태 갱신
            #============================================================

            machine_available_time[
                machine_id
            ] = end_time


            job_available_time[
                job_id
            ] = end_time


            next_operation_index[
                job_id
            ] += 1


        return schedule



    #============================================================
    # Particle Velocity / Position 갱신
    #============================================================

    def _update_particle(
        self,
        particle,
        global_best_os_position,
        global_best_ms_position
    ):

        #============================================================
        # OS Position / Velocity 갱신
        #============================================================

        for i in range(
            len(particle["os_position"])
        ):

            #PSO의 랜덤 계수
            r1 = random.random()
            r2 = random.random()


            #============================================================
            # Velocity 공식
            #============================================================

            #v(t+1)
            #
            #= w * v(t)
            #
            #+ c1 * r1 * (pbest - x)
            #
            #+ c2 * r2 * (gbest - x)

            new_velocity = (

                self.inertia_weight
                * particle["os_velocity"][i]

                +

                self.cognitive_coefficient
                * r1
                * (
                    particle[
                        "best_os_position"
                    ][i]

                    -

                    particle[
                        "os_position"
                    ][i]
                )

                +

                self.social_coefficient
                * r2
                * (
                    global_best_os_position[i]

                    -

                    particle[
                        "os_position"
                    ][i]
                )
            )


            #============================================================
            # Velocity 제한
            #============================================================

            new_velocity = max(
                -self.max_velocity,
                min(
                    self.max_velocity,
                    new_velocity
                )
            )


            particle[
                "os_velocity"
            ][i] = new_velocity


            #============================================================
            # Position 갱신
            #============================================================

            #x(t+1) = x(t) + v(t+1)

            new_position = (
                particle[
                    "os_position"
                ][i]

                + new_velocity
            )


            #Random-Key가 0~1 범위를 유지하도록 제한
            new_position = max(
                0.0,
                min(
                    1.0,
                    new_position
                )
            )


            particle[
                "os_position"
            ][i] = new_position


        #============================================================
        # MS Position / Velocity 갱신
        #============================================================

        for i in range(
            len(particle["ms_position"])
        ):

            r1 = random.random()
            r2 = random.random()


            new_velocity = (

                self.inertia_weight
                * particle["ms_velocity"][i]

                +

                self.cognitive_coefficient
                * r1
                * (
                    particle[
                        "best_ms_position"
                    ][i]

                    -

                    particle[
                        "ms_position"
                    ][i]
                )

                +

                self.social_coefficient
                * r2
                * (
                    global_best_ms_position[i]

                    -

                    particle[
                        "ms_position"
                    ][i]
                )
            )


            #Velocity 제한
            new_velocity = max(
                -self.max_velocity,
                min(
                    self.max_velocity,
                    new_velocity
                )
            )


            particle[
                "ms_velocity"
            ][i] = new_velocity


            #Position 갱신
            new_position = (
                particle[
                    "ms_position"
                ][i]

                + new_velocity
            )


            #0~1 범위 유지
            new_position = max(
                0.0,
                min(
                    1.0,
                    new_position
                )
            )


            particle[
                "ms_position"
            ][i] = new_position