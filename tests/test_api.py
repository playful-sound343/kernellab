import importlib

from fastapi.testclient import TestClient


def test_run_history_compare_stats_and_snapshot_import(tmp_path, monkeypatch):
    monkeypatch.setenv("KERNELLAB_DB", str(tmp_path / "api.db"))
    import kernellab.api as api
    api = importlib.reload(api)
    workload = {"quantum": 2, "processes": [{"pid": "P1", "arrival": 0, "burst": 5}, {"pid": "P2", "arrival": 1, "burst": 2}]}
    with TestClient(api.app) as client:
        first = client.post("/run", json={"module": "cpu", "algorithm": "fcfs", "params": workload})
        second = client.post("/run", json={"module": "cpu", "algorithm": "sjf", "params": workload})
        assert first.status_code == second.status_code == 200
        history = client.get("/history", params={"module": "cpu"}).json()
        assert history[0]["workload_id"] == history[1]["workload_id"]
        comparison = client.get("/compare", params={"module": "cpu", "metric": "avg_waiting_time", "workload_id": history[0]["workload_id"]})
        assert comparison.status_code == 200
        assert comparison.json()[0]["rank"] == 1
        statistics = client.get("/stats").json()
        waiting_rows = [row for row in statistics if row["metric_name"] == "avg_waiting_time"]
        assert {row["algorithm"] for row in waiting_rows} == {"fcfs", "sjf"}
        assert all(row["runs"] == 1 for row in waiting_rows)
        imported = client.post("/snapshots/import", json={"taken_at": "2026-11-21T00:00:00+00:00", "source": "WindowsProbe", "processes": [{"pid": "1", "name": "Browser", "rss_bytes": 100}]})
        assert imported.status_code == 200
        assert imported.json()["process_count"] == 1
