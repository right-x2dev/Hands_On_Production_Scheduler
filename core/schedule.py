#스케줄링 결과 한 건, 전체 스케줄 표현하기. 

class ScheduleEntry:
    def __init__(
        self,
        job_id,
        operation_id,
        machine_id,
        start_time,
        end_time
    ):
        self.job_id = job_id
        self.operation_id = operation_id
        self.machine_id = machine_id
        self.start_time = start_time
        self.end_time = end_time

    def __repr__(self):
        return (
            f"ScheduleEntry("
            f"job={self.job_id}, "
            f"operation={self.operation_id}, "
            f"machine={self.machine_id}, "
            f"start={self.start_time}, "
            f"end={self.end_time}"
            f")"
        )


class Schedule:
    def __init__(self):
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def get_entries(self):
        return self.entries

    def __repr__(self):
        return "\n".join(str(entry) for entry in self.entries)





