#3번째. 
#여러 operation을 하나의 작업으로 묶고, 그 순서를 보존.
class Job:
    def __init__(self, job_id, operations):
        self.job_id = job_id
        self.operations = operations
        self.due_date = due_date

    def get_operations(self):
        return self.operations

    def get_operation(self, index):
        return self.operations[index]

    def __repr__(self):
        return (
            f"Job("
            f"id={self.job_id}, "
            f"due_date={self.due_date}, "
            f"operations={self.operations}"
            f")"
        )