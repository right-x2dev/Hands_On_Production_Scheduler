from data.sample_instance import create_sample_instance
from algorithms.fifo import FIFOScheduler
from evaluation.kpi import calculate_makespan
from visualization.gantt import draw_gantt

machines, jobs = create_sample_instance()

scheduler = FIFOScheduler()

schedule = scheduler.solve(
    machines = machines,
    jobs = jobs
)


print(schedule)

makespan = calculate_makespan(schedule)


print()
print("Makespan:", makespan)


#이제, FJSP문제->Machine선택->시작시간 계산 -> 실제 생산 Schedule 

draw_gantt(schedule)