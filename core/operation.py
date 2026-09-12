#2번째
#하나의 operation이 여러 machine에서 처리될 수 있고, machineakek 처리시간이 다를 수 있다. 


class Operation:
    def __init__(self, operation_id, processing_times):
        self.operation_id = operation_id
        self.processing_times = processing_times

    def get_available_machines(self):
        return list(self.processing_times.keys())

    def get_processing_time(self, machine_id):
        return self.processing_times[machine_id]

    def __repr__(self):
        return (
            f"Operation("
            #작업 번호. 011의 경우 1번 job의 1번 operation을 의미.
            f"id={self.operation_id}, "
            # 각 기계에서의 처리 시간
            f"processing_times={self.processing_times}"
            f")"
        )
