from kernellab.deadlock import find_cycle, bankers
from kernellab.memory import buddy_allocate, page_replace


def test_fifo_belady_anomaly_example():
    references = [1,2,3,4,1,2,5,1,2,3,4,5]
    assert page_replace(references, 4, "fifo").metrics["page_faults"] > page_replace(references, 3, "fifo").metrics["page_faults"]


def test_wait_for_cycle(): assert find_cycle({"P1":["P2"], "P2":["P1"]}) == ["P1", "P2", "P1"]


def test_bankers_safe_sequence():
    result = bankers([3,3,2], [[7,5,3],[3,2,2],[9,0,2],[2,2,2],[4,3,3]], [[0,1,0],[2,0,0],[3,0,2],[2,1,1],[0,0,2]])
    assert result.metrics["safe"] == 1


def test_buddy_rounds_request_to_power_of_two_block():
    result = buddy_allocate(32, [5, 8])
    assert result.details["placements"][0]["block_size"] == 8
