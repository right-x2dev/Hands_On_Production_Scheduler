#3번째. 
#여러 operation을 하나의 작업으로 묶고, 그 순서를 보존.
class Job:
    def __init__(self, job_id, operations):
        self.job_id = job_id
        self.operations = operations

    def get_operations(self):
        return self.operations

    def get_operation(self, index):
        return self.operations[index]

    def __repr__(self):
        return (
            f"Job("
            f"id={self.job_id}, "
            f"operations={self.operations}"
            f")"
        )