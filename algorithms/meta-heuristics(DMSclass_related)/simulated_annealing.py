#ScheduleEntry = 작업 하나의 배정 결과
#Schedule = 여러 배정 결과를 모아놓은 전체 일정
from core.schedule import Schedule, ScheduleEntry

#Makespan 계산
from evaluation.kpi import calculate_makespan

import random
import math


#============================================================
# Simulated Annealing + FJSP
#============================================================

#Simulated Annealing(SA)은 현재 Solution 하나에서 시작해서
#조금씩 변형된 Neighbor Solution을 생성하면서 탐색하는 메타휴리스틱.
#
#1. 초기 Solution 생성
#2. Neighbor Solution 생성
#3. 현재해와 Neighbor의 Makespan 비교
#4. Neighbor가 더 좋으면 무조건 이동
#5. Neighbor가 더 나빠도 일정 확률로 이동
#6. Temperature 감소
#7. 반복
#
#목적함수:
#Makespan 최소화


class SimulatedAnnealingScheduler:

    def __init__(
        self,
        initial_temperature=100.0,
        cooling_rate=0.95,
        minimum_temperature=0.1,
        max_iterations=500
    ):

        #처음 Temperature
        self.initial_temperature = initial_temperature

        #Temperature 감소율
        #예: 100 -> 95 -> 90.25 ...
        self.cooling_rate = cooling_rate

        #Temperature가 이 값보다 작아지면 탐색 종료
        self.minimum_temperature = minimum_temperature

        #최대 반복 횟수
        self.max_iterations = max_iterations

        #최종 최적 결과 저장
        self.best_makespan = float("inf")
        self.best_solution = None


    #============================================================
    # 전체 Simulated Annealing 실행
    #============================================================

    def solve(self, machines, jobs):

        #============================================================
        # 1. 초기 Solution 생성
        #============================================================

        current_solution = self._create_initial_solution(
            jobs
        )

        #초기 Solution을 실제 Schedule로 변환
        current_schedule = self._decode(
            current_solution,
            machines,
            jobs
        )

        #초기 Makespan 계산
        current_makespan = calculate_makespan(
            current_schedule
        )


        #초기 Solution을 우선 Best Solution으로 설정
        best_solution = {
            "os": current_solution["os"].copy(),
            "ms": current_solution["ms"].copy()
        }

        best_schedule = current_schedule
        best_makespan = current_makespan


        #============================================================
        # 2. 초기 Temperature 설정
        #============================================================

        temperature = self.initial_temperature


        #============================================================
        # 3. Simulated Annealing 반복
        #============================================================

        iteration = 0

        while (
            temperature > self.minimum_temperature
            and iteration < self.max_iterations
        ):

            #============================================================
            # 4. 현재 Solution에서 Neighbor 하나 생성
            #============================================================

            neighbor_solution = self._generate_neighbor(
                current_solution,
                jobs
            )


            #Neighbor를 실제 FJSP Schedule로 변환
            neighbor_schedule = self._decode(
                neighbor_solution,
                machines,
                jobs
            )


            #Neighbor Makespan 계산
            neighbor_makespan = calculate_makespan(
                neighbor_schedule
            )


            #============================================================
            # 5. 현재해와 Neighbor의 차이 계산
            #============================================================

            #Makespan 최소화 문제이므로:
            #
            #delta < 0
            #→ Neighbor가 더 좋음
            #
            #delta > 0
            #→ Neighbor가 더 나쁨

            delta = (
                neighbor_makespan
                - current_makespan
            )


            #============================================================
            # 6. Neighbor 수용 여부 결정
            #============================================================

            #Neighbor가 더 좋은 경우
            if delta < 0:

                accept = True


            #Neighbor가 더 나쁜 경우
            else:

                #Simulated Annealing의 핵심
                #
                #P = exp(-delta / T)
                #
                #Temperature가 높을수록
                #나쁜 해도 받아들일 가능성이 높음.
                #
                #Temperature가 낮아지면
                #나쁜 해를 거의 받아들이지 않음.

                acceptance_probability = math.exp(
                    -delta / temperature
                )

                random_value = random.random()

                accept = (
                    random_value
                    < acceptance_probability
                )


            #============================================================
            # 7. Neighbor를 받아들이면 현재해 갱신
            #============================================================

            if accept:

                current_solution = neighbor_solution
                current_schedule = neighbor_schedule
                current_makespan = neighbor_makespan


            #============================================================
            # 8. 전역 Best Solution 갱신
            #============================================================

            if current_makespan < best_makespan:

                best_makespan = current_makespan

                best_solution = {
                    "os": current_solution["os"].copy(),
                    "ms": current_solution["ms"].copy()
                }

                best_schedule = current_schedule


            #============================================================
            # 9. Temperature 감소
            #============================================================

            temperature *= self.cooling_rate


            #반복 횟수 증가
            iteration += 1


        #최종 결과 저장
        self.best_makespan = best_makespan
        self.best_solution = best_solution

        return best_schedule



    #============================================================
    # 초기 Solution 생성
    #============================================================

    def _create_initial_solution(self, jobs):

        #============================================================
        # Operation Sequence(OS)
        #============================================================

        #예:
        #
        #J1 = O11, O12
        #J2 = O21, O22
        #J3 = O31, O32
        #
        #OS:
        #
        #[J1, J2, J3, J1, J2, J3]
        #
        #같은 Job이 다시 등장하면
        #그 Job의 다음 Operation을 의미함.

        operation_sequence = []


        #가장 Operation이 많은 Job의 Operation 개수
        max_operations = max(
            len(job.operations)
            for job in jobs
        )


        #Operation 단계별로 Job 넣기
        for op_index in range(max_operations):

            for job in jobs:

                if op_index < len(job.operations):

                    operation_sequence.append(
                        job.job_id
                    )


        #============================================================
        # Machine Selection(MS)
        #============================================================

        machine_selection = {}


        for job in jobs:

            for op_index, operation in enumerate(
                job.operations
            ):

                #초기 Machine은
                #Processing Time이 가장 짧은 Machine 선택
                best_machine = min(
                    operation.processing_times,
                    key=operation.processing_times.get
                )

                machine_selection[
                    (job.job_id, op_index)
                ] = best_machine


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
        # SPT / EDD와 동일한 FJSP 상태 관리
        #============================================================

        #각 Machine이 언제부터 사용가능?
        machine_available_time = {
            machine.machine_id: 0
            for machine in machines
        }


        #각 Job의 직전 Operation 종료시간
        job_available_time = {
            job.job_id: 0
            for job in jobs
        }


        #각 Job에서 다음 처리 Operation index
        next_operation_index = {
            job.job_id: 0
            for job in jobs
        }


        #Job ID로 Job 객체를 찾기 위한 dictionary
        job_dict = {
            job.job_id: job
            for job in jobs
        }


        #============================================================
        # OS 순서대로 Schedule 생성
        #============================================================

        for job_id in solution["os"]:

            job = job_dict[job_id]


            #현재 Job에서 다음 처리 Operation
            op_index = next_operation_index[
                job_id
            ]


            operation = job.operations[
                op_index
            ]


            #Machine Selection에서 저장된 Machine 확인
            machine_id = solution["ms"][
                (job_id, op_index)
            ]


            #해당 Machine의 Processing Time
            processing_time = (
                operation.get_processing_time(
                    machine_id
                )
            )


            #============================================================
            # 시작 시간 계산
            #============================================================

            #작업은:
            #1. 이전 Operation이 끝나야 함.
            #2. Machine이 비어있어야 함.
            #
            #둘 중 더 늦은 시간부터 시작.

            start_time = max(
                job_available_time[job_id],
                machine_available_time[machine_id]
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


            schedule.add_entry(entry)


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
    # Neighbor Solution 하나 생성
    #============================================================

    def _generate_neighbor(
        self,
        solution,
        jobs
    ):

        #현재 Solution 복사
        neighbor = {
            "os": solution["os"].copy(),
            "ms": solution["ms"].copy()
        }


        #============================================================
        # Neighbor 생성 방법을 랜덤하게 선택
        #============================================================

        #0 → OS Swap
        #1 → Machine 변경

        move_type = random.choice(
            [0, 1]
        )


        #============================================================
        # Neighbor Type 1
        # Operation Sequence(OS) Swap
        #============================================================

        if move_type == 0:

            os = neighbor["os"]


            #서로 다른 Job이 있는 위치들을 후보로 찾기
            valid_pairs = []

            for i in range(len(os)):

                for j in range(i + 1, len(os)):

                    #같은 Job끼리 swap하면
                    #실제 OS 의미가 변하지 않으므로 제외.
                    if os[i] != os[j]:

                        valid_pairs.append(
                            (i, j)
                        )


            #유효한 pair가 있다면 하나 랜덤 선택
            if valid_pairs:

                i, j = random.choice(
                    valid_pairs
                )


                #두 위치 Swap
                neighbor["os"][i], neighbor["os"][j] = (
                    neighbor["os"][j],
                    neighbor["os"][i]
                )


        #============================================================
        # Neighbor Type 2
        # Machine Assignment 변경
        #============================================================

        else:

            #Machine 선택을 바꿀 수 있는 Operation 후보 저장
            changeable_operations = []


            for job in jobs:

                for op_index, operation in enumerate(
                    job.operations
                ):

                    #가능한 Machine이 2개 이상일 때만
                    #Machine 변경 가능
                    if len(
                        operation.get_available_machines()
                    ) > 1:

                        changeable_operations.append(
                            (
                                job,
                                op_index,
                                operation
                            )
                        )


            if changeable_operations:

                #변경할 Operation 하나 랜덤 선택
                job, op_index, operation = random.choice(
                    changeable_operations
                )


                current_machine = neighbor["ms"][
                    (job.job_id, op_index)
                ]


                #현재 Machine을 제외한 다른 Machine 후보
                machine_candidates = [
                    machine
                    for machine
                    in operation.get_available_machines()

                    if machine != current_machine
                ]


                #새 Machine 랜덤 선택
                new_machine = random.choice(
                    machine_candidates
                )


                neighbor["ms"][
                    (job.job_id, op_index)
                ] = new_machine


        return neighbor