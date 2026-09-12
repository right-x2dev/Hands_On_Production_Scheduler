import matplotlib.pyplot as plt

def draw_gantt(schedule):
    entries = schedule.get_entries()


    if not entries:
        print("Schedule is empty.")
        return

    # Machines 목록 추출
    machines = sorted(
        set(entry.machine_id for entry in entries)
    )


    #Machine y축 위치 저장
    machine_y = {
        machine_id: index
        for index, machine_id in enumerate(machine_ids)
    }


    fig, ax = plt.subplots()

    for entry in entries:
        y = machine_y[entry.machine_id]

        duration = entry.end_time - entry.start_time

        #가로 막대 그리는 함수
        ax.barh(
            y=y,
            width=duration,
            left=entry.start_time
        )

        ax.text(
            entry.start_time + duration / 2,
            y,
            f"{entry.job_id}-{entry.operation_id}",
            ha="center",
            va="center"
        )
    ax.set_yticks(range(len(machine_ids)))
    ax.set_yticklabels(machine_ids)

    ax.set_xlabel("Time")
    ax.set_ylabel("Machine")
    ax.set_title("Production Schedule Gantt Chart")

    ax.grid(axis="x", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.show()
    
