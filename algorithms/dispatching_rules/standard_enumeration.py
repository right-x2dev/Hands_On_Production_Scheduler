#기준.
#브루토포스
# (1) 후보 operation을 전부 탐색. 
# (2) 머신도 전부 탐색
# (3) 재귀
# (4) 끝까지 갔다가.
# (5) 백트래킹
# (6) 다른 경우 탐색


#ScheduleEntry = 작업 하나의 배정 결과
#Schedule = 여러 배정 결과를 모아놓은 전체 일정
from core.schedule import Schedule, ScheduleEntry


#============================================================
# Enumeration 스케줄러
#============================================================

#Enumeration스케줄러. solve()에 생산문제 넣으면 최종 스케줄 변환함.
#입력: machines, jobs || 출력: schedule

#스케줄러 알고리즘(FJSP-Enumeration)
#가능한 Operation 선택 순서 + 가능한 Machine 배정 조합을 모두 탐색.
#1. 각 Job의 다음 Operation만 후보로 가져옴.
#2. 후보 Operation 중 하나를 선택하는 모든 경우를 탐색
#3. 해당 Operation이 사용 가능한 모든 Machine을 탐색
#4. Schedule에 임시 저장
#5. Job/Machine 상태 갱신
#6. 다음 단계로 재귀 탐색
#7. 탐색 후 상태를 원래대로 되돌림(Backtracking)
#8. 모든 조합 중 Makespan이 가장 작은 스케줄 저장


class EnumerationScheduler:

    def __init__(self):

        #현재까지 찾은 가장 좋은 Makespan.
        #처음에는 아직 최적해를 모르기 때문에 무한대로 설정.
        self.best_makespan = float("inf")

        #현재까지 찾은 가장 좋은 스케줄의 ScheduleEntry들을 저장.
        self.best_entries = None


    def solve(self, machines, jobs):

        #============================================================
        # FJSP 상태 초기화
        #============================================================

        #각 머신이 언제부터 사용가능?
        #1. 머신 상태 저장. 처음에는 모든 머신이 0시부터 비어있다고 봄.
        #M1->M2->.....
        machine_available_time = {
            machine.machine_id: 0
            for machine in machines
        }


        # 각 Job의 직전 Operation 종료시간.
        #2. 각 Job의 이전 Operation이 언제 끝났는지 나타냄.
        job_available_time = {
            job.job_id: 0
            for job in jobs
        }

        #각 Job에서, 다음에 처리해야 하는 Operation의 index
        #각 Job에서 다음으로 처리해야 하는 Operation번호 기억.
        next_operation_index = {
            job.job_id: 0
            for job in jobs
        }


        #============================================================
        # Enumeration에서는 여기부터 SPT와 다름
        #============================================================

        #solve()를 여러 번 실행할 수도 있기 때문에
        #기존에 저장되어 있던 최적해 정보를 초기화.
        #Makespan, Entries 두 가지 챙기기.
        self.best_makespan = float("inf")
        self.best_entries = None


        #Enumeration은 while문으로 하나씩 선택하는 것이 아니라,
        #재귀함수 _search()를 이용해 가능한 모든 경우를 탐색함.
        self._search(
            jobs=jobs,
            machine_available_time=machine_available_time,
            job_available_time=job_available_time,
            next_operation_index=next_operation_index,
            current_entries=[]
        )


        #============================================================
        # 탐색이 끝난 후, 최적 결과를 Schedule 객체로 변환
        #============================================================

        #빈 스케줄 하나 생성, 최적 배정 결과를 여기에 넣을 것.
        schedule = Schedule()

        #최적 스케줄을 찾았다면 하나씩 Schedule에 추가.
        if self.best_entries is not None:

            for entry in self.best_entries:
                schedule.add_entry(entry)

        return schedule



    #============================================================
    # Enumeration의 핵심: 재귀 완전탐색 함수
    # 작업들, 머신 가용가능 시간시점, 잡 시작가능 시간시점, 다음 오퍼레이션 인덱스, 현재 엔트리 
    #============================================================

    def _search(
        self,
        jobs,
        machine_available_time,
        job_available_time,
        next_operation_index,
        current_entries
    ):


        #============================================================
        # 1. 모든 Operation의 스케줄링이 끝났는지 확인
        #============================================================

        all_scheduled = True

        for job in jobs:

            #아직 다음에 처리해야 할 Operation이 남아있다면
            #모든 작업이 끝난 것이 아님.
            if next_operation_index[job.job_id] < len(job.operations):

                all_scheduled = False
                break


        #모든 Operation의 배정이 끝났다면 현재 스케줄 평가.
        if all_scheduled:

            #현재 ScheduleEntry들 중
            #가장 늦게 끝난 Operation의 종료시간 = Makespan.
            makespan = max(
                (entry.end_time for entry in current_entries),
                default=0
            )

            #현재 스케줄이 지금까지 찾은 최적해보다 좋다면 갱신.
            if makespan < self.best_makespan:

                self.best_makespan = makespan

                #현재 리스트를 그대로 저장하면 이후 Backtracking 과정에서
                #변경되므로 복사해서 저장.
                self.best_entries = list(current_entries)

            #하나의 완성된 스케줄을 검사했으므로
            #이 재귀 경로는 종료.
            return


        #============================================================
        # 2. Branch and Bound 형태의 간단한 가지치기
        #============================================================

        #현재까지 만든 부분 스케줄만 봐도
        #이미 기존 최적 Makespan 이상이라면
        #이 뒤를 더 탐색해도 더 좋아질 수 없으므로 중단.
        if current_entries:

            current_makespan = max(
                entry.end_time
                for entry in current_entries
            )

            if current_makespan >= self.best_makespan:
                return


        #============================================================
        # 3. 현재 처리 가능한 Operation 후보 탐색
        #============================================================

        #각 Job에서, 현재 다음 operation만 후보로 가져옴
        for job in jobs:

            #각 job을 하나씩 보면서, 현재 실행 가능한 operation찾기.
            op_index = next_operation_index[job.job_id]

            # 해당 Job의 모든 Operation이 끝났다면 제외
            # operation이 2개면 인덱스번호는 각각 0, 1.
            if op_index >= len(job.operations):
                continue


            #현재 처리해야 할 Operation가져오기.
            operation = job.operations[op_index]


            #============================================================
            # SPT와 가장 큰 차이 1:
            # 하나의 Operation을 선택하지 않고 모든 후보를 탐색함.
            #============================================================

            #SPT:
            #가장 짧은 processing_time의 Operation 하나만 선택.
            #
            #Enumeration:
            #현재 가능한 모든 Job의 다음 Operation을
            #for문을 통해 하나씩 전부 시도함.


            #============================================================
            # 4. 가능한 모든 Machine을 하나씩 시도
            #============================================================

            # 선택된 Operation을 어떤 Machine에 배치할지 결정
            # Enumeration에서는 가장 빨리 끝나는 Machine 하나만 고르지 않고
            # 사용 가능한 모든 Machine을 하나씩 탐색.
            for machine_id in operation.get_available_machines():

                #머신별 처리시간 가져오기.
                processing_time = (
                    operation.get_processing_time(machine_id)
                )

                # 시작 가능 시간 계산.
                #작업시작에는 두 조건이 필요함
                #(1) 그 Job의 이전 Operation이 끝나야 함.
                #(2) 머신이 비어있어야 함.
                #예: J2이전작업종료=5, M1사용가능시간시점=3.
                #=> max(5, 3) -> 5시에 시작.
                start_time = max(
                    job_available_time[job.job_id],
                    machine_available_time[machine_id]
                )


                #시작시간 + 처리시간 = 종료시간.
                end_time = start_time + processing_time


                #============================================================
                # 5. Backtracking을 위해 현재 상태 저장
                #============================================================

                #잠시 뒤 이 Machine 배정을 취소하고
                #다른 경우도 탐색해야 하므로 기존 값을 기억해 둠.
                previous_machine_time = (
                    machine_available_time[machine_id]
                )

                previous_job_time = (
                    job_available_time[job.job_id]
                )


                #============================================================
                # 6. 현재 선택을 Schedule에 임시 저장
                #============================================================

                # 스케줄러에 결과 저장
                #객체예시
                #J2-O21(job_id(잡 번호), operation_id(작업 번호))
                #M1 (머신 번호)
                #0~2 (시작시간~끝나는시간)
                entry = ScheduleEntry(
                    job_id=job.job_id,
                    operation_id=operation.operation_id,
                    machine_id=machine_id,
                    start_time=start_time,
                    end_time=end_time
                )


                #현재 탐색 중인 Schedule에 추가.
                current_entries.append(entry)


                # 상태 갱신
                # O21이 M1에서 0~2동안 실행됐다면 => M1 = 2
                #(M1은 2시 이전에는 다른작업받기 불가능)
                machine_available_time[machine_id] = end_time

                #J2의 O21이 2시에 끝남.
                job_available_time[job.job_id] = end_time

                #J2는 이제
                # operations[0] = O21완료
                #했으므로, next_operation_index["J2"] = 1
                #다음 후보는 O22가 된다.
                next_operation_index[job.job_id] += 1


                #============================================================
                # 7. 현재 선택을 기준으로 다음 단계 탐색
                #============================================================

                #현재 Operation/Machine 배정을 한 상태에서
                #그 다음 가능한 모든 경우를 다시 탐색.
                self._search(
                    jobs=jobs,
                    machine_available_time=machine_available_time,
                    job_available_time=job_available_time,
                    next_operation_index=next_operation_index,
                    current_entries=current_entries
                )


                #============================================================
                # 8. Backtracking
                #============================================================

                #위 선택으로 시작하는 모든 경우를 탐색했으므로
                #방금 넣었던 ScheduleEntry 제거.
                current_entries.pop()


                #Machine 상태를 선택 이전으로 복원.
                machine_available_time[machine_id] = (
                    previous_machine_time
                )

                #Job 상태를 선택 이전으로 복원.
                job_available_time[job.job_id] = (
                    previous_job_time
                )

                #Operation index 역시 하나 전으로 되돌림.
                next_operation_index[job.job_id] -= 1