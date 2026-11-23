from kernellab.models import Process
from kernellab.scheduling import FCFSScheduler, RoundRobinScheduler, SRTFScheduler


def workload(): return [Process("P1", 0, 5), Process("P2", 1, 3), Process("P3", 2, 1)]


def test_fcfs_hand_computed_waiting_time():
    result = FCFSScheduler().run(workload())
    assert result.metrics["avg_waiting_time"] == 10 / 3
    assert result.details["processes"][1]["finish"] == 8


def test_round_robin_completes_all_processes():
    assert RoundRobinScheduler().run(workload(), quantum=2).metrics["makespan"] == 9


def test_srtf_has_no_worse_average_wait_than_fcfs_for_this_workload():
    assert SRTFScheduler().run(workload()).metrics["avg_waiting_time"] <= FCFSScheduler().run(workload()).metrics["avg_waiting_time"]
