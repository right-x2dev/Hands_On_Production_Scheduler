from core.schedule import Schedule, ScheduleEntry


class FIFOScheduler:
    def solve(self, machines, jobs):

        schedule = Schedule()

        # 각 Machine이 몇 시부터 사용 가능한지 저장
        machine_available_time = {
            machine.machine_id: 0
            for machine in machines
        }

        # 각 Job의 직전 Operation이 언제 끝났는지 저장
        job_available_time = {
            job.job_id: 0
            for job in jobs
        }

        # Job을 입력된 순서대로 처리
        for job in jobs:

            # 같은 Job 안에서는 Operation 순서대로 처리
            for operation in job.operations:

                best_machine = None
                best_start_time = None
                best_end_time = None

                # 이 Operation을 처리할 수 있는 Machine들을 비교
                for machine_id in operation.get_available_machines():

                    processing_time = operation.get_processing_time(machine_id)

                    # Operation은
                    # 1. 이전 Operation이 끝나야 하고
                    # 2. Machine도 비어 있어야 시작 가능
                    start_time = max(
                        job_available_time[job.job_id],
                        machine_available_time[machine_id]
                    )

                    end_time = start_time + processing_time

                    # 가장 빨리 끝낼 수 있는 Machine 선택
                    if best_end_time is None or end_time < best_end_time:
                        best_machine = machine_id
                        best_start_time = start_time
                        best_end_time = end_time

                # 스케줄 결과 저장
                entry = ScheduleEntry(
                    job_id=job.job_id,
                    operation_id=operation.operation_id,
                    machine_id=best_machine,
                    start_time=best_start_time,
                    end_time=best_end_time
                )

                schedule.add_entry(entry)

                # 선택된 Machine의 다음 사용 가능 시간 갱신
                machine_available_time[best_machine] = best_end_time

                # 해당 Job의 다음 Operation은 이 작업이 끝난 뒤 시작 가능
                job_available_time[job.job_id] = best_end_time

        return schedule