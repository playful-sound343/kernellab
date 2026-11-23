from kernellab.memory import allocate


def test_first_and_worst_fit_choose_earliest_largest_block_while_best_fit_chooses_smallest():
    blocks, requests = [100, 500, 200], [120]
    first = allocate(blocks, requests, "first_fit")
    best = allocate(blocks, requests, "best_fit")
    worst = allocate(blocks, requests, "worst_fit")
    assert first.details["placements"][0]["start"] == 100
    assert best.details["placements"][0]["start"] == 600
    assert worst.details["placements"][0]["start"] == 100


def test_allocation_reports_failure_when_no_free_block_fits():
    result = allocate([32], [16, 20], "first_fit")
    assert result.metrics["failure_rate"] == 0.5
    assert result.events[-1].event_type == "allocation_failed"
