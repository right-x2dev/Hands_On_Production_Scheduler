def calculate_makespan(schedule):
    entries = schedule.get_entries()


    if not entries:
        return 0


    return max(entry.end_time for entry in entries)



#Makespan: 전체 생산계획을 완료하는데 걸리는 시간