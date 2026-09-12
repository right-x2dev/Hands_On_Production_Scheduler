from data.sample_instance import create_sample_instance

machines, jobs = create_sample_instance()

print("Machines")
for machine in machines:
    print(machine)

print()

print("Jobs")
for job in jobs:
    print(job)