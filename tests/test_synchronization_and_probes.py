from kernellab.probes import FakeProbe, stamped_snapshot
from kernellab.synchronization import dining_philosophers, producer_consumer, race_condition_lab


def test_producer_consumer_records_blocked_operations():
    result = producer_consumer(1, ["consume", "produce", "produce", "consume"])
    assert result.metrics["blocked_operations"] == 2
    assert result.metrics["final_buffer_size"] == 0


def test_ordered_dining_philosophers_completes_without_deadlock():
    result = dining_philosophers(rounds=3, philosophers=5)
    assert result.metrics == {"total_meals": 15.0, "deadlocks": 0.0}


def test_protected_thread_lab_has_no_lost_updates():
    assert race_condition_lab(workers=2, iterations=100).metrics["lost_updates"] == 0


def test_fake_probe_snapshot_has_source_and_processes():
    captured = stamped_snapshot(FakeProbe([{"pid": 10, "name": "editor", "memory": 64}]))
    assert captured["source"] == "FakeProbe"
    assert captured["processes"][0]["name"] == "editor"
