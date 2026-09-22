#ScheduleEntry = 작업 하나의 배정 결과
#Schedule = 여러 배정 결과를 모아놓은 전체 일정
from core.schedule import Schedule, ScheduleEntry

#Makespan 계산
from evaluation.kpi import calculate_makespan

import random


#============================================================
# Genetic Algorithm + FJSP
#============================================================

#Genetic Algorithm(GA)은 여러 개의 Solution(Individual)을
#Population으로 가지고 탐색하는 메타휴리스틱.
#
#1. 초기 Population 생성
#2. 각 Individual의 Makespan 평가
#3. 좋은 Individual을 Parent로 선택
#4. Parent끼리 Crossover
#5. Mutation
#6. 새로운 Population 생성
#7. 여러 Generation 반복
#
#목적함수:
#Makespan 최소화


class GeneticAlgorithmScheduler:

    def __init__(
        self,
        population_size=50,
        generations=100,
        crossover_rate=0.8,
        mutation_rate=0.2,
        tournament_size=3
    ):

        #한 Generation에 존재하는 Individual 개수
        self.population_size = population_size

        #몇 Generation 동안 진화할 것인지
        self.generations = generations

        #Crossover 수행 확률
        self.crossover_rate = crossover_rate

        #Mutation 수행 확률
        self.mutation_rate = mutation_rate

        #Tournament Selection에서
        #몇 개의 Individual을 뽑아 경쟁시킬 것인지
        self.tournament_size = tournament_size


        #최종 결과 저장용
        self.best_solution = None
        self.best_makespan = float("inf")


    #============================================================
    # 전체 Genetic Algorithm 실행
    #============================================================

    def solve(self, machines, jobs):

        #============================================================
        # 1. 초기 Population 생성
        #============================================================

        population = self._create_initial_population(
            jobs
        )


        best_solution = None
        best_schedule = None
        best_makespan = float("inf")


        #============================================================
        # 2. Generation 반복
        #============================================================

        for generation in range(self.generations):

            evaluated_population = []


            #============================================================
            # Population의 모든 Individual 평가
            #============================================================

            for individual in population:

                #Solution → 실제 Schedule
                schedule = self._decode(
                    individual,
                    machines,
                    jobs
                )

                #Makespan 계산
                makespan = calculate_makespan(
                    schedule
                )


                evaluated_population.append(
                    (
                        individual,
                        schedule,
                        makespan
                    )
                )


                #============================================================
                # 전역 Best Solution 갱신
                #============================================================

                if makespan < best_makespan:

                    best_makespan = makespan

                    best_solution = {
                        "os": individual["os"].copy(),
                        "ms": individual["ms"].copy()
                    }

                    best_schedule = schedule


            #============================================================
            # Makespan이 작은 순서대로 정렬
            #============================================================

            evaluated_population.sort(
                key=lambda x: x[2]
            )


            #============================================================
            # 3. 새로운 Population 생성
            #============================================================

            new_population = []


            #============================================================
            # Elitism
            #============================================================

            #현재 Generation에서 가장 좋은 Individual 하나는
            #Crossover/Mutation 없이 다음 세대로 그대로 넘김.
            elite = evaluated_population[0][0]

            new_population.append(
                {
                    "os": elite["os"].copy(),
                    "ms": elite["ms"].copy()
                }
            )


            #============================================================
            # 새로운 Population이 가득 찰 때까지 반복
            #============================================================

            while len(new_population) < self.population_size:

                #============================================================
                # 4. Parent Selection
                #============================================================

                parent1 = self._tournament_selection(
                    evaluated_population
                )

                parent2 = self._tournament_selection(
                    evaluated_population
                )


                #============================================================
                # 5. Crossover
                #============================================================

                if random.random() < self.crossover_rate:

                    child1, child2 = self._crossover(
                        parent1,
                        parent2,
                        jobs
                    )

                else:

                    #Crossover를 하지 않으면
                    #Parent를 그대로 복사.
                    child1 = {
                        "os": parent1["os"].copy(),
                        "ms": parent1["ms"].copy()
                    }

                    child2 = {
                        "os": parent2["os"].copy(),
                        "ms": parent2["ms"].copy()
                    }


                #============================================================
                # 6. Mutation
                #============================================================

                child1 = self._mutate(
                    child1,
                    jobs
                )

                child2 = self._mutate(
                    child2,
                    jobs
                )


                #새 Population에 추가
                new_population.append(
                    child1
                )


                #Population 크기를 넘지 않는 경우에만
                #두 번째 Child 추가
                if len(new_population) < self.population_size:

                    new_population.append(
                        child2
                    )


            #============================================================
            # 다음 Generation으로 이동
            #============================================================

            population = new_population


        #============================================================
        # 최종 결과 저장
        #============================================================

        self.best_solution = best_solution
        self.best_makespan = best_makespan

        return best_schedule



    #============================================================
    # 초기 Population 생성
    #============================================================

    def _create_initial_population(self, jobs):

        population = []


        #============================================================
        # 기본 OS 생성
        #============================================================

        #예:
        #
        #J1 = O11, O12
        #J2 = O21, O22
        #J3 = O31, O32
        #
        #기본 OS:
        #
        #[J1, J2, J3, J1, J2, J3]

        base_os = []


        max_operations = max(
            len(job.operations)
            for job in jobs
        )


        for op_index in range(max_operations):

            for job in jobs:

                if op_index < len(job.operations):

                    base_os.append(
                        job.job_id
                    )


        #============================================================
        # Population 생성
        #============================================================

        for individual_index in range(
            self.population_size
        ):

            #============================================================
            # OS 생성
            #============================================================

            os = base_os.copy()


            #첫 번째 Individual은
            #기본 OS를 그대로 유지.
            #
            #나머지는 순서를 랜덤하게 섞어서
            #Population 다양성 확보.
            if individual_index != 0:

                random.shuffle(os)


            #============================================================
            # MS 생성
            #============================================================

            ms = {}


            for job in jobs:

                for op_index, operation in enumerate(
                    job.operations
                ):

                    available_machines = (
                        operation.get_available_machines()
                    )


                    #첫 번째 Individual은
                    #Processing Time이 가장 짧은 Machine 사용.
                    if individual_index == 0:

                        machine = min(
                            operation.processing_times,
                            key=operation.processing_times.get
                        )


                    #나머지 Individual은
                    #가능한 Machine 중 랜덤 선택.
                    else:

                        machine = random.choice(
                            available_machines
                        )


                    ms[
                        (job.job_id, op_index)
                    ] = machine


            population.append(
                {
                    "os": os,
                    "ms": ms
                }
            )


        return population



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
        # SPT / EDD / Tabu / SA와 동일한 FJSP 상태 관리
        #============================================================

        #각 Machine이 언제부터 사용 가능한지
        machine_available_time = {
            machine.machine_id: 0
            for machine in machines
        }


        #각 Job의 이전 Operation 종료시간
        job_available_time = {
            job.job_id: 0
            for job in jobs
        }


        #각 Job에서 다음으로 처리해야 하는 Operation index
        next_operation_index = {
            job.job_id: 0
            for job in jobs
        }


        #Job ID → Job 객체
        job_dict = {
            job.job_id: job
            for job in jobs
        }


        #============================================================
        # OS 순서대로 실제 Schedule 생성
        #============================================================

        for job_id in solution["os"]:

            job = job_dict[
                job_id
            ]


            #현재 Job에서 처리해야 하는 Operation
            op_index = next_operation_index[
                job_id
            ]


            operation = job.operations[
                op_index
            ]


            #MS에서 선택된 Machine
            machine_id = solution["ms"][
                (job_id, op_index)
            ]


            #해당 Machine에서의 Processing Time
            processing_time = (
                operation.get_processing_time(
                    machine_id
                )
            )


            #============================================================
            # 시작 시간 계산
            #============================================================

            #작업 시작에는:
            #
            #1. 이전 Operation이 끝나야 함
            #2. Machine이 비어있어야 함
            #
            #따라서 둘 중 더 늦은 시점부터 시작.

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
    # Tournament Selection
    #============================================================

    def _tournament_selection(
        self,
        evaluated_population
    ):

        #Population에서 몇 개를 랜덤 선택.
        competitors = random.sample(
            evaluated_population,
            min(
                self.tournament_size,
                len(evaluated_population)
            )
        )


        #Makespan이 가장 작은 Individual 선택.
        winner = min(
            competitors,
            key=lambda x: x[2]
        )


        individual = winner[0]


        #원본이 수정되지 않도록 복사해서 반환.
        return {
            "os": individual["os"].copy(),
            "ms": individual["ms"].copy()
        }



    #============================================================
    # Crossover
    #============================================================

    def _crossover(
        self,
        parent1,
        parent2,
        jobs
    ):

        #============================================================
        # OS Crossover
        #============================================================

        #FJSP의 OS에는 같은 Job이 Operation 개수만큼 반복됨.
        #
        #단순한 일반 1-point crossover를 사용하면
        #특정 Job의 개수가 달라질 수 있으므로 사용하면 안 됨.
        #
        #여기서는 Job-Based Crossover를 사용.
        #
        #Job 일부를 선택해서 Parent1의 위치를 그대로 가져오고,
        #나머지 Job들은 Parent2의 순서를 이용해 채움.

        job_ids = [
            job.job_id
            for job in jobs
        ]


        #Job ID 일부 랜덤 선택
        selected_jobs = set(
            random.sample(
                job_ids,
                random.randint(
                    1,
                    max(1, len(job_ids) - 1)
                )
            )
        )


        child1_os = [None] * len(
            parent1["os"]
        )

        child2_os = [None] * len(
            parent2["os"]
        )


        #============================================================
        # Child 1
        #============================================================

        #선택된 Job들은 Parent1 위치 그대로 유지
        for i, job_id in enumerate(
            parent1["os"]
        ):

            if job_id in selected_jobs:

                child1_os[i] = job_id


        #선택되지 않은 Job들은
        #Parent2의 등장 순서대로 채움
        remaining_from_parent2 = [
            job_id
            for job_id in parent2["os"]
            if job_id not in selected_jobs
        ]


        remaining_index = 0


        for i in range(len(child1_os)):

            if child1_os[i] is None:

                child1_os[i] = (
                    remaining_from_parent2[
                        remaining_index
                    ]
                )

                remaining_index += 1


        #============================================================
        # Child 2
        #============================================================

        #동일하게 Parent2를 기준으로 Selected Job 유지
        for i, job_id in enumerate(
            parent2["os"]
        ):

            if job_id in selected_jobs:

                child2_os[i] = job_id


        remaining_from_parent1 = [
            job_id
            for job_id in parent1["os"]
            if job_id not in selected_jobs
        ]


        remaining_index = 0


        for i in range(len(child2_os)):

            if child2_os[i] is None:

                child2_os[i] = (
                    remaining_from_parent1[
                        remaining_index
                    ]
                )

                remaining_index += 1


        #============================================================
        # MS Crossover
        #============================================================

        child1_ms = {}
        child2_ms = {}


        for job in jobs:

            for op_index, operation in enumerate(
                job.operations
            ):

                key = (
                    job.job_id,
                    op_index
                )


                #각 Operation마다
                #Parent1 / Parent2 Machine 중 하나 선택.
                if random.random() < 0.5:

                    child1_ms[key] = (
                        parent1["ms"][key]
                    )

                    child2_ms[key] = (
                        parent2["ms"][key]
                    )

                else:

                    child1_ms[key] = (
                        parent2["ms"][key]
                    )

                    child2_ms[key] = (
                        parent1["ms"][key]
                    )


        child1 = {
            "os": child1_os,
            "ms": child1_ms
        }

        child2 = {
            "os": child2_os,
            "ms": child2_ms
        }


        return child1, child2



    #============================================================
    # Mutation
    #============================================================

    def _mutate(
        self,
        individual,
        jobs
    ):

        #복사본 생성
        mutated = {
            "os": individual["os"].copy(),
            "ms": individual["ms"].copy()
        }


        #============================================================
        # OS Mutation
        #============================================================

        if random.random() < self.mutation_rate:

            os = mutated["os"]


            #서로 다른 Job이 위치한 pair 후보
            valid_pairs = []


            for i in range(len(os)):

                for j in range(i + 1, len(os)):

                    if os[i] != os[j]:

                        valid_pairs.append(
                            (i, j)
                        )


            if valid_pairs:

                i, j = random.choice(
                    valid_pairs
                )


                #두 Job 위치 Swap
                os[i], os[j] = (
                    os[j],
                    os[i]
                )


        #============================================================
        # Machine Selection Mutation
        #============================================================

        if random.random() < self.mutation_rate:

            changeable_operations = []


            #Machine 후보가 2개 이상인 Operation 찾기
            for job in jobs:

                for op_index, operation in enumerate(
                    job.operations
                ):

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

                job, op_index, operation = random.choice(
                    changeable_operations
                )


                key = (
                    job.job_id,
                    op_index
                )


                current_machine = mutated["ms"][
                    key
                ]


                #현재 Machine을 제외한 다른 후보
                machine_candidates = [
                    machine_id
                    for machine_id
                    in operation.get_available_machines()

                    if machine_id != current_machine
                ]


                new_machine = random.choice(
                    machine_candidates
                )


                mutated["ms"][
                    key
                ] = new_machine


        return mutated