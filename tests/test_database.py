from kernellab.database import RunStore
from kernellab.models import SimulationResult


def test_store_history_and_compare(tmp_path):
    store = RunStore(tmp_path / "lab.db")
    run_id = store.save("cpu", {"processes": []}, SimulationResult("cpu", "fcfs", {"avg_waiting_time": 2.0}))
    second_id = store.save("cpu", {"processes": []}, SimulationResult("cpu", "sjf", {"avg_waiting_time": 1.0}))
    history = store.history("cpu")
    assert history[0]["id"] == second_id
    assert history[0]["workload_id"] == history[1]["workload_id"]
    assert run_id != second_id
    assert store.compare("cpu", "avg_waiting_time")[0]["rank"] == 1
