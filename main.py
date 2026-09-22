# ============================================================
# Hands-On Production Scheduler
#
# 지금까지 만든 모든 FJSP 알고리즘을
# 동일한 문제 Instance에서 실행하고 성능을 비교한다.
# ============================================================

import time
import random

import numpy as np


# ============================================================
# 문제 Instance
# ============================================================

from data.sample_instance import create_sample_instance


# ============================================================
# Evaluation / Visualization
# ============================================================

from evaluation.kpi import calculate_makespan
from visualization.gantt import draw_gantt


# ============================================================
# Dispatching Rules
# ============================================================

from algorithms.fifo import FIFOScheduler
from algorithms.spt import SPTScheduler
from algorithms.edd import EDDScheduler


# ============================================================
# Exact Search
# ============================================================

from algorithms.enumeration import EnumerationScheduler


# ============================================================
# Metaheuristics
# ============================================================

from algorithms.tabu_search import TabuSearchScheduler

from algorithms.simulated_annealing import (
    SimulatedAnnealingScheduler
)

from algorithms.genetic_algorithm import (
    GeneticAlgorithmScheduler
)

from algorithms.particle_swarm_optimization import (
    ParticleSwarmOptimizationScheduler
)


# ============================================================
# Deep Reinforcement Learning
# ============================================================

from algorithms.reinforcement_learning.dqn import (
    DQNScheduler
)

from algorithms.reinforcement_learning.gnn_ppo import (
    GNNPPOScheduler
)


# ============================================================
# Random Seed
# ============================================================

# GA / SA / Tabu / PSO / RL은 랜덤성이 있으므로
# 같은 실험을 다시 수행했을 때 결과를 비교하기 쉽도록
# Seed를 고정한다.

RANDOM_SEED = 42


def set_random_seed(seed):

    random.seed(seed)

    np.random.seed(seed)

    # PyTorch가 설치되어 있을 경우
    # PyTorch random seed도 설정
    try:
        import torch

        torch.manual_seed(seed)

    except ImportError:
        pass


# ============================================================
# 알고리즘 하나 실행
# ============================================================

def run_algorithm(
    algorithm_name,
    scheduler,
    machines,
    jobs
):

    print()
    print("=" * 70)

    print(
        f"Running: {algorithm_name}"
    )

    print("=" * 70)


    # --------------------------------------------------------
    # 실행시간 측정 시작
    # --------------------------------------------------------

    start_time = time.perf_counter()


    # --------------------------------------------------------
    # Scheduler 실행
    # --------------------------------------------------------

    schedule = scheduler.solve(
        machines,
        jobs
    )


    # --------------------------------------------------------
    # 실행시간 측정 종료
    # --------------------------------------------------------

    end_time = time.perf_counter()

    elapsed_time = (
        end_time
        - start_time
    )


    # --------------------------------------------------------
    # Makespan 평가
    # --------------------------------------------------------

    makespan = calculate_makespan(
        schedule
    )


    # --------------------------------------------------------
    # 결과 출력
    # --------------------------------------------------------

    print(
        f"Makespan     : {makespan}"
    )

    print(
        f"Execution Time: "
        f"{elapsed_time:.4f} sec"
    )


    return {
        "algorithm": algorithm_name,
        "schedule": schedule,
        "makespan": makespan,
        "time": elapsed_time
    }


# ============================================================
# 결과 비교 출력
# ============================================================

def print_comparison(results):

    print()
    print()
    print("=" * 75)
    print("                ALGORITHM COMPARISON")
    print("=" * 75)


    # Makespan 기준 정렬
    sorted_results = sorted(
        results,
        key=lambda x: x["makespan"]
    )


    print(
        f"{'Algorithm':<30}"
        f"{'Makespan':>15}"
        f"{'Time(sec)':>15}"
    )

    print("-" * 75)


    for result in sorted_results:

        print(
            f"{result['algorithm']:<30}"
            f"{result['makespan']:>15}"
            f"{result['time']:>15.4f}"
        )


    print("-" * 75)


    # --------------------------------------------------------
    # 가장 좋은 결과
    # --------------------------------------------------------

    best_result = sorted_results[0]


    print()

    print(
        "Best Algorithm :",
        best_result["algorithm"]
    )

    print(
        "Best Makespan  :",
        best_result["makespan"]
    )


    return best_result


# ============================================================
# Main
# ============================================================

def main():

    # ========================================================
    # 1. Random Seed 설정
    # ========================================================

    set_random_seed(
        RANDOM_SEED
    )


    # ========================================================
    # 2. FJSP Instance 생성
    # ========================================================

    machines, jobs = (
        create_sample_instance()
    )


    print()
    print("=" * 70)

    print(
        "Hands-On Production Scheduler"
    )

    print("=" * 70)

    print(
        "Number of Machines:",
        len(machines)
    )

    print(
        "Number of Jobs:",
        len(jobs)
    )

    print(
        "Number of Operations:",
        sum(
            len(job.operations)
            for job in jobs
        )
    )


    # ========================================================
    # 3. 사용할 Scheduler 정의
    # ========================================================

    schedulers = [


        # ----------------------------------------------------
        # Dispatching Rules
        # ----------------------------------------------------

        (
            "FIFO",
            FIFOScheduler()
        ),

        (
            "SPT",
            SPTScheduler()
        ),

        (
            "EDD",
            EDDScheduler()
        ),


        # ----------------------------------------------------
        # Exact Search
        # ----------------------------------------------------

        (
            "Enumeration",
            EnumerationScheduler()
        ),


        # ----------------------------------------------------
        # Metaheuristics
        # ----------------------------------------------------

        (
            "Tabu Search",

            TabuSearchScheduler(
                max_iterations=100,
                tabu_tenure=7
            )
        ),


        (
            "Simulated Annealing",

            SimulatedAnnealingScheduler(
                initial_temperature=100.0,
                cooling_rate=0.95,
                minimum_temperature=0.1,
                max_iterations=500
            )
        ),


        (
            "Genetic Algorithm",

            GeneticAlgorithmScheduler(
                population_size=50,
                generations=100,
                crossover_rate=0.8,
                mutation_rate=0.2,
                tournament_size=3
            )
        ),


        (
            "Particle Swarm Optimization",

            ParticleSwarmOptimizationScheduler(
                num_particles=30,
                max_iterations=100,
                inertia_weight=0.7,
                cognitive_coefficient=1.5,
                social_coefficient=1.5,
                max_velocity=0.2
            )
        ),


        # ----------------------------------------------------
        # Deep Reinforcement Learning
        # ----------------------------------------------------

        (
            "DQN",

            DQNScheduler(
                episodes=1000,
                gamma=0.99,
                learning_rate=0.001,
                batch_size=64,
                epsilon_start=1.0,
                epsilon_end=0.05,
                epsilon_decay=0.995,
                target_update_interval=20
            )
        ),


        (
            "GNN + PPO",

            GNNPPOScheduler(
                episodes=1000,
                gamma=0.99,
                learning_rate=0.0003,
                clip_epsilon=0.2,
                update_epochs=5
            )
        )
    ]


    # ========================================================
    # 4. 모든 알고리즘 실행
    # ========================================================

    results = []


    for (
        algorithm_name,
        scheduler
    ) in schedulers:

        try:

            # 알고리즘마다 같은 Seed에서 시작하도록
            # 다시 초기화
            set_random_seed(
                RANDOM_SEED
            )


            result = run_algorithm(
                algorithm_name,
                scheduler,
                machines,
                jobs
            )


            results.append(
                result
            )


        # ----------------------------------------------------
        # 특정 알고리즘에서 오류가 나더라도
        # 나머지 알고리즘은 계속 실행
        # ----------------------------------------------------

        except Exception as error:

            print()

            print(
                f"[ERROR] "
                f"{algorithm_name}"
            )

            print(
                error
            )


    # ========================================================
    # 5. 알고리즘 성능 비교
    # ========================================================

    if not results:

        print(
            "실행에 성공한 알고리즘이 없습니다."
        )

        return


    best_result = print_comparison(
        results
    )


    # ========================================================
    # 6. 가장 좋은 Schedule 출력
    # ========================================================

    print()
    print("=" * 75)

    print(
        "BEST SCHEDULE"
    )

    print("=" * 75)


    print(
        best_result["schedule"]
    )


    # ========================================================
    # 7. Best Schedule Gantt Chart
    # ========================================================

    draw_gantt(
        best_result["schedule"]
    )


# ============================================================
# Python Entry Point
# ============================================================

if __name__ == "__main__":

    main()