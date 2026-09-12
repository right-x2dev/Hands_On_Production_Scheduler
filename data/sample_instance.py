from core.machine import Machine
from core.operation import Operation
from core.job import Job


def create_sample_instance():
    # 1. 설비 생성
    machines = [
        Machine("M1"),
        Machine("M2"),
        Machine("M3")
    ]

    # 2. Job 1
    job1 = Job(
        job_id="J1",
        operations=[
            Operation(
                operation_id="O11",
                processing_times={
                    "M1": 3,
                    "M2": 4
                }
            ),
            Operation(
                operation_id="O12",
                processing_times={
                    "M2": 2,
                    "M3": 3
                }
            )
        ]
    )

    # 3. Job 2
    job2 = Job(
        job_id="J2",
        operations=[
            Operation(
                operation_id="O21",
                processing_times={
                    "M1": 2,
                    "M3": 4
                }
            ),
            Operation(
                operation_id="O22",
                processing_times={
                    "M2": 5,
                    "M3": 3
                }
            )
        ]
    )

    # 4. Job 3
    job3 = Job(
        job_id="J3",
        operations=[
            Operation(
                operation_id="O31",
                processing_times={
                    "M2": 4
                }
            ),
            Operation(
                operation_id="O32",
                processing_times={
                    "M1": 3,
                    "M3": 2
                }
            )
        ]
    )

    jobs = [job1, job2, job3]

    return machines, jobs