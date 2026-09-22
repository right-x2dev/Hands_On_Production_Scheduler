#메타 휴리스틱1: 타부 서치
#메타휴리스틱: 해를 만들어놓고, 주변 해를 탐색

#ScheduleEntry = 작업 하나의 배정 결과
#Schedule = 여러 배정 결과를 모아놓은 전체 일정
from core.schedule import Schedule, ScheduleEntry

#Makespan 계산
from evaluation.kpi import calculate_makespan


#============================================================
# Tabu Search + FJSP
#============================================================

#Tabu Search는 SPT/EDD처럼 작업 하나를 선택하고 바로 확정하는 방식이 아님.
#
#1. 초기 Solution 생성
#2. 현재 Solution 주변의 Neighbor Solution들을 생성
#3. 각 Solution을 실제 Schedule로 변환(Decode)
#4. Makespan 평가
#5. 가장 좋은 Neighbor로 이동
#6. 방금 수행한 이동을 Tabu List에 저장(일정시간동안 금기시)
#7. 일정 횟수 반복
#
#목적함수:
#Makespan 최소화

#공정을 하나씩 확정하는 알고리즘이 아니라, 
#'완성된 스케줄 후보' 자체를 계속 수정하는 알고리즘

#Solution 내부에...
#OS: Operation Sequence => 공정들을 어떤 순서로 고려할 것인가?
#MS: Machine Selection => 각 공정을 어느 Machine에 넣을 것인가?

#코드 구조
# 타부서치 스케줄러 클래스
# -- 타부서치 본체 함수
# -- 1. 초기 해 생성 함수
# -- 2. 디코드 함수
# -- 3. 이웃 해 생성함수

class TabuSearchScheduler:
    #(1) 알고리즘  (최대 반복횟수, 재탐색 금지 지속 시간(금기시되는 시간))
    def __init__(
        self,
        max_iterations=100,
        tabu_tenure=7
    ):

        #Tabu Search를 몇 번 반복할 것인지
        self.max_iterations = max_iterations

        #한 번 Tabu가 된 move를 몇 iteration 동안 금지할 것인지
        self.tabu_tenure = tabu_tenure

        #최종 결과 저장용 (아직 메이크스팬 안나옴. 결과적으로 최소화해야함. 솔루션도 아직 없음)
        self.best_makespan = float("inf")
        self.best_solution = None


    #============================================================
    # 전체 Tabu Search 실행
    #============================================================
    #(2) 타부 서치 본체
    # 입력은 machines, jobs || 출력은 최종 best Schedule
    def solve(self, machines, jobs):

        #============================================================
        # 1. 초기 Solution 생성 (출발점 만들기)
        #============================================================
        #하나의 정상적인 FJSP 해 만들기.
        current_solution = self._create_initial_solution(jobs)

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


        #현재 초기해를 일단 최적해로 설정
        best_solution = {
            "os": current_solution["os"].copy(),
            "ms": current_solution["ms"].copy()
        }

        best_schedule = current_schedule
        best_makespan = current_makespan


        #============================================================
        # 2. Tabu List
        #============================================================

        #key = 금지할 move
        #value = 몇 번째 iteration까지 Tabu인지
        #{금지할 move index? : 몇번째 iteration까지 tabu}
        tabu_list = {}


        #============================================================
        # 3. Tabu Search 반복
        #1. 현재해 주변 Neighbor 생성
        #2. 각 Neighbor 평가
        #3. Tabu 여부 확인
        #4. 가장 좋은 Neighbor 선택
        #5. 그 Neighbor로 이동
        #6. Tabu List 갱신
        #7. 전역 최적해 갱신
        #============================================================

        for iteration in range(self.max_iterations):

            #현재 Solution의 Neighbor들을 생성
            neighbors = self._generate_neighbors(
                current_solution,
                jobs
            )


            #이번 iteration에서 선택할 최적 Neighbor
            best_candidate_solution = None
            # 그 솔루션을 디코드 한 실제 스케줄
            best_candidate_schedule = None
            best_candidate_makespan = float("inf")

            #선택된 move가 무엇인지 저장
            best_candidate_tabu_add = None


            #============================================================
            # Neighbor 하나씩 평가
            #============================================================
            # 튜플 세 개짜리. 
            for (
                neighbor,
                tabu_check_move,
                tabu_add_move
            ) in neighbors:
                
                #neighbor: 실제로 평가할 새 솔루션
                #tabu_check_move: 이 neighbor로 가는 행동이 현재 타부인가? 확인시 사용
                #tabu_add_move: 위의 거에 해당하면 여기에 저장한다.


                #Neighbor Solution을 실제 생산 Schedule로 변환
                #neighbor solution => neighbor schedule
                neighbor_schedule = self._decode(
                    neighbor,
                    machines,
                    jobs
                )


                #Neighbor의 Makespan 계산
                neighbor_makespan = calculate_makespan(
                    neighbor_schedule
                )


                #============================================================
                # Tabu 여부 확인
                #============================================================
                #언제까지 이 스케줄은 타부인가요..?
                # -1은 만약 해당 move가 타부리스트에 없으면...
                tabu_until = tabu_list.get(
                    tabu_check_move,
                    -1
                )

                is_tabu = tabu_until > iteration


                #============================================================
                # Aspiration Criterion
                # Tabu인 행동이라도, 엄청 좋은 결과를 만든다면 예외적으로 허용
                # 여기서는 지금까지의 최고 기록을 깨버린다면이 기준. 
                #============================================================

                #Tabu Move라 하더라도
                #전역 최적해보다 더 좋은 결과를 만들면 허용.
                aspiration = (
                    neighbor_makespan < best_makespan
                )


                #Tabu인데 Aspiration 조건도 만족하지 못하면 제외
                #이 move가 타부이고, 동시에 전역최적해를 갱신할 정도로 좋지도 않다면, 이 neighbor는 버린다. 
                if is_tabu and not aspiration:
                    continue


                #============================================================
                # 현재까지 본 Neighbor 중 가장 좋은 것 선택
                #============================================================

                if neighbor_makespan < best_candidate_makespan:

                    best_candidate_solution = neighbor

                    best_candidate_schedule = (
                        neighbor_schedule
                    )

                    best_candidate_makespan = (
                        neighbor_makespan
                    )

                    best_candidate_tabu_add = (
                        tabu_add_move
                    )


            #선택 가능한 Neighbor가 없으면 탐색 종료
            #모든 neighbor가 예를 들어 tabu라서 제거되어버리면, 
            #best_candidate_solution이 처음값인 none 그대로일 수 있음.
            #그러면 더 이상 이동할 곳이 없으므로..
            if best_candidate_solution is None:
                break


            #============================================================
            # 4. 선택된 Neighbor로 이동
            #============================================================

            current_solution = best_candidate_solution
            current_schedule = best_candidate_schedule
            current_makespan = best_candidate_makespan


            #============================================================
            # 5. 방금 수행한 Move를 Tabu List에 등록
            #============================================================

            tabu_list[best_candidate_tabu_add] = (
                iteration + self.tabu_tenure
            )


            #============================================================
            # 6. 전역 최적해 갱신
            #============================================================

            if current_makespan < best_makespan:

                best_makespan = current_makespan

                best_solution = {
                    "os": current_solution["os"].copy(),
                    "ms": current_solution["ms"].copy()
                }

                best_schedule = current_schedule


            #============================================================
            # 오래된 Tabu Move 제거
            #============================================================
            #tabu_list에 있는 move들을 하나씩 보면서, 
            #만료 iteration이 현재 iteration보다 작거나 같으면,
            #expired_moves에 넣어라. 
            expired_moves = [
                move
                for move, expiry in tabu_list.items()
                if expiry <= iteration
            ]
            #만료된 move 실제 삭제. 
            for move in expired_moves:
                del tabu_list[move]


        #최종 결과 저장
        self.best_makespan = best_makespan
        self.best_solution = best_solution

        return best_schedule


#여기부터 9월 17에 하기...
    #============================================================
    # 초기 Solution 생성 함수
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


        #가장 긴 Job의 Operation 개수
        max_operations = max(
            len(job.operations)
            for job in jobs
        )


        #Operation 단계별로 Job들을 넣음.
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
                #Processing Time이 가장 짧은 Machine 선택.
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
    # Solution → 실제 FJSP Schedule 변환 (디코드 함수)
    #============================================================

    def _decode(
        self,
        solution,
        machines,
        jobs
    ):

        schedule = Schedule()


        #============================================================
        # SPT / EDD와 동일한 FJSP 상태 관리 개념
        #============================================================

        #각 머신이 언제부터 사용 가능?
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


        #Job ID로 Job 객체를 빠르게 찾기 위한 dictionary
        job_dict = {
            job.job_id: job
            for job in jobs
        }


        #============================================================
        # Operation Sequence 순서대로 실제 Schedule 생성
        #============================================================

        for job_id in solution["os"]:

            job = job_dict[job_id]


            #현재 Job에서 다음 Operation index
            op_index = next_operation_index[job_id]


            #현재 처리해야 할 Operation
            operation = job.operations[op_index]


            #Solution에 저장된 Machine 배정 확인
            machine_id = solution["ms"][
                (job_id, op_index)
            ]


            #머신별 Processing Time
            processing_time = (
                operation.get_processing_time(
                    machine_id
                )
            )


            #============================================================
            # SPT / EDD와 동일한 시간 계산
            #============================================================

            #작업시작 조건:
            #
            #1. 이전 Operation 종료
            #2. Machine 사용 가능
            #
            #둘 중 더 늦은 시간부터 시작.
            start_time = max(
                job_available_time[job_id],
                machine_available_time[machine_id]
            )


            #종료시간
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
    # Neighbor Solution 생성 (이웃 해 생성함수)
    #============================================================

    def _generate_neighbors(
        self,
        solution,
        jobs
    ):

        neighbors = []


        #============================================================
        # Neighbor Type 1
        # Operation Sequence(OS) Swap
        #============================================================

        os = solution["os"]


        for i in range(len(os)):

            for j in range(i + 1, len(os)):


                #같은 Job끼리 바꾸면 결과가 동일하므로 제외.
                if os[i] == os[j]:
                    continue


                new_os = os.copy()

                #두 위치 Swap
                new_os[i], new_os[j] = (
                    new_os[j],
                    new_os[i]
                )


                neighbor = {
                    "os": new_os,
                    "ms": solution["ms"].copy()
                }


                #Swap은 다시 같은 위치를 Swap하면
                #원래 상태로 돌아오므로 자기 자신이 역연산.
                tabu_move = (
                    "swap",
                    i,
                    j
                )


                neighbors.append(
                    (
                        neighbor,
                        tabu_move,
                        tabu_move
                    )
                )


        #============================================================
        # Neighbor Type 2
        # Machine Assignment 변경
        #============================================================

        for job in jobs:

            for op_index, operation in enumerate(
                job.operations
            ):

                current_machine = solution["ms"][
                    (job.job_id, op_index)
                ]


                #현재 Operation이 사용 가능한 Machine들을 확인.
                for new_machine in (
                    operation.get_available_machines()
                ):


                    #현재 Machine과 같으면 변화가 없으므로 제외.
                    if new_machine == current_machine:
                        continue


                    new_ms = solution["ms"].copy()


                    new_ms[
                        (job.job_id, op_index)
                    ] = new_machine


                    neighbor = {
                        "os": solution["os"].copy(),
                        "ms": new_ms
                    }


                    #현재 move:
                    #M1 → M2
                    tabu_check_move = (
                        "machine",
                        job.job_id,
                        op_index,
                        current_machine,
                        new_machine
                    )


                    #Tabu List에는 역방향을 저장.
                    #
                    #방금 M1 → M2를 했으면
                    #바로 M2 → M1로 되돌아가지 못하게 함.
                    tabu_add_move = (
                        "machine",
                        job.job_id,
                        op_index,
                        new_machine,
                        current_machine
                    )


                    neighbors.append(
                        (
                            neighbor,
                            tabu_check_move,
                            tabu_add_move
                        )
                    )


        return neighbors


