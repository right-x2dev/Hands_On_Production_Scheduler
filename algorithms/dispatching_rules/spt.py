
#ScheduleEntry = 작업 하나의 배정 결과
#Schedule = 여러 배정 결과를 모아놓은 전체 일정
from core.schedule import Schedule, ScheduleEntry

#SPT스케줄러. solve()에 생산문제 넣으면 최종 스케줄 변환함. 
#입력: machines, jobs || 출력: schedule

#스케줄러 알고리즘(FJSP-SPT)
#SPT 기반 operation dispatching + earliest completion time기반 machine 할당.
#1. 각 Job의 다음 Operation만 꺼냄.
#2. 가장 짦은 processing_time을 가진 Operation 선택
#3. 그 Operation을 가장 빨리 완료할 수 있는 머신 선택
#4. Schedule 저장.
#5. Job/Machine 상태 갱신. 

#FJSP에서는 Operation마다 Machine별 Processing_time이 다르기 때문에,
#우리는 min(operation.processing_times.values())를 SPT 기준으로 사용.
#머신 선택은 별도로 earliest completion time기준으로 하는 중. 


class SPTScheduler:
    def solve(self, machines, jobs):
        
        #빈 스케줄 하나 생성, 작업 하나씩 배정할 때마다 여기에 넣을것.
        schedule = Schedule()
        
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
        
        #4. 전체 Operation개수 
        #Job1에 3개, Job2에 2개 => 총 opearion은 5개. 
        total_operations = sum(
            len(job.operations)
            for job in jobs
        )
        
        #반복문 시작
        #지금까지 몇개 스케줄링했는지 세는 변수. 
        scheduled_count = 0
        
        #모든 작업 끝날때까지 반복. 
        while scheduled_count < total_operations:
            
            #후보 operation생성. SPT가 비교할 후보들을 담을 리스트. 
            candidates = []
            
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

                # FJSP에서는 Machine마다 processing time이 다르므로
                # 가능한 Machine 중 가장 짧은 processing time을
                # SPT 기준값으로 사용
                shortest_processing_time = min(
                    operation.processing_times.values()
                )

                #리스트에 이런 튜플 저장!
                candidates.append(
                    (
                        shortest_processing_time,
                        job,
                        operation
                    )
                )

            # processing time이 가장 짧은 Operation 선택
            # 가장 짧은 Operation 선택. 
            #튜플 첫 번째 값: 즉 shortest processing time 기준으로 정렬. 
            candidates.sort(key=lambda x: x[0])
            # 첫번째 후보를 선택. 
            #_의 경우 이후에는 직접 필요없어서 _로 받은거. 
            _, selected_job, selected_operation = candidates[0]


            #Machine선택. 
            #현재 최선의 머신 후보를 저장할 변수들. 
            best_machine = None
            best_start_time = None
            best_end_time = None

            # 선택된 Operation을 어떤 Machine에 배치할지 결정
            for machine_id in selected_operation.get_available_machines():

                #머신별 처리시간 가져오기. 
                processing_time = (
                    selected_operation.get_processing_time(machine_id)
                )

                # 시작 가능 시간 계산. 
                #작업시작에는 두 조건이 필요함
                #(1) 그 Job의 이전 Operation이 끝나야 함. 
                #(2) 머신이 비어있어야 함. 
                #예: J2이전작업종료=5, M1사용가능시간시점=3. 
                #=> max(5, 3) -> 5시에 시작. 
                start_time = max(
                    job_available_time[selected_job.job_id],
                    machine_available_time[machine_id]
                )


                #시작시간 + 처리시간 = 종료시간. 
                end_time = start_time + processing_time

                # 가장 빨리 끝나는 Machine 선택
                #현재 머신이 지금까지 본 머신보다 더 빨리 끝난다=>선택.
                if best_end_time is None or end_time < best_end_time:
                    best_machine = machine_id
                    best_start_time = start_time
                    best_end_time = end_time

            # 스케줄러에 결과 저장
            #객체예시
            #J2-O21(job_id(잡 번호), operation_id(작업 번호))
            #M1 (머신 번호)
            #0~2 (시작시간~끝나는시간)
            entry = ScheduleEntry(
                job_id=selected_job.job_id,
                operation_id=selected_operation.operation_id,
                machine_id=best_machine,
                start_time=best_start_time,
                end_time=best_end_time
            )


            #전체 Schedule에 추가. 
            schedule.add_entry(entry)

            # 상태 갱신
            # O21이 M1에서 0~2동안 실행됐다면 => M1 = 2 (M1은 2시 이전에는 다른작업받기 불가능)
            machine_available_time[best_machine] = best_end_time
            #J2의 O21이 2시에 끝남. 
            job_available_time[selected_job.job_id] = best_end_time

            #J2는 이제 
            # opeartions[0] = O21완료
            #했으므로, next_operation_index["J2"] = 1
            #다음 후보는 O22가 된다. 
            next_operation_index[selected_job.job_id] += 1

            #한 작업 끝냈으므로=> 0->1
            scheduled_count += 1

        return schedule
    