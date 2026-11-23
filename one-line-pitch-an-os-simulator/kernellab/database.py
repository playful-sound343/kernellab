from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import SimulationResult


SCHEMA = """
CREATE TABLE IF NOT EXISTS workloads (id INTEGER PRIMARY KEY, seed INTEGER, kind TEXT NOT NULL, params_json TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS runs (id INTEGER PRIMARY KEY, workload_id INTEGER NOT NULL REFERENCES workloads(id), module TEXT NOT NULL, algorithm TEXT NOT NULL, created_at TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS metrics (id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES runs(id), metric_name TEXT NOT NULL, value REAL NOT NULL);
CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY, run_id INTEGER NOT NULL REFERENCES runs(id), tick INTEGER NOT NULL, event_type TEXT NOT NULL, payload_json TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS snapshots (id INTEGER PRIMARY KEY, taken_at TEXT NOT NULL, source TEXT NOT NULL, process_json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS idx_runs_workload_module ON runs(workload_id, module);
CREATE INDEX IF NOT EXISTS idx_metrics_run_name ON metrics(run_id, metric_name);
"""


class RunStore:
    def __init__(self, path: str | Path | None = None) -> None:
        self.path = str(path or os.getenv("KERNELLAB_DB", "data/kernellab.db"))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn: conn.executescript(SCHEMA)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path); conn.row_factory = sqlite3.Row; conn.execute("PRAGMA foreign_keys = ON"); return conn

    def save(self, kind: str, params: dict[str, Any], result: SimulationResult, seed: int | None = None) -> int:
        now = datetime.now(timezone.utc).isoformat()
        params_json = json.dumps(params, sort_keys=True, separators=(",", ":"))
        with self.connect() as conn:
            # Identical workloads share an ID, making algorithm comparisons meaningful.
            existing = conn.execute("SELECT id FROM workloads WHERE kind = ? AND params_json = ? ORDER BY id LIMIT 1", (kind, params_json)).fetchone()
            workload_id = existing["id"] if existing else conn.execute("INSERT INTO workloads(seed, kind, params_json, created_at) VALUES (?, ?, ?, ?)", (seed, kind, params_json, now)).lastrowid
            run_id = conn.execute("INSERT INTO runs(workload_id, module, algorithm, created_at) VALUES (?, ?, ?, ?)", (workload_id, result.module, result.algorithm, now)).lastrowid
            conn.executemany("INSERT INTO metrics(run_id, metric_name, value) VALUES (?, ?, ?)", [(run_id, k, v) for k, v in result.metrics.items()])
            conn.executemany("INSERT INTO events(run_id, tick, event_type, payload_json) VALUES (?, ?, ?, ?)", [(run_id, e.tick, e.event_type, json.dumps(e.payload)) for e in result.events])
            return int(run_id)

    def history(self, module: str | None = None, algorithm: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
        filters, values = [], []
        if module: filters.append("r.module = ?"); values.append(module)
        if algorithm: filters.append("r.algorithm = ?"); values.append(algorithm)
        where = " WHERE " + " AND ".join(filters) if filters else ""
        values.append(limit)
        with self.connect() as conn:
            rows = conn.execute(f"SELECT r.id, r.workload_id, r.module, r.algorithm, r.created_at, w.kind, w.params_json FROM runs r JOIN workloads w ON r.workload_id=w.id{where} ORDER BY r.id DESC LIMIT ?", values).fetchall()
            return [dict(row) | {"metrics": dict(conn.execute("SELECT metric_name, value FROM metrics WHERE run_id=?", (row["id"],)).fetchall())} for row in rows]

    def compare(self, module: str, metric: str, workload_id: int | None = None) -> list[dict[str, Any]]:
        clause, values = "r.module = ? AND m.metric_name = ?", [module, metric]
        if workload_id is not None: clause += " AND r.workload_id = ?"; values.append(workload_id)
        with self.connect() as conn:
            return [dict(x) for x in conn.execute(f"SELECT r.id, r.workload_id, r.algorithm, m.value, RANK() OVER (ORDER BY m.value ASC) AS rank FROM runs r JOIN metrics m ON m.run_id=r.id WHERE {clause} ORDER BY rank, r.id", values)]

    def stats(self) -> list[dict[str, Any]]:
        with self.connect() as conn:
            return [dict(x) for x in conn.execute("SELECT r.module, r.algorithm, m.metric_name, COUNT(*) AS runs, ROUND(AVG(m.value), 4) AS average_value, RANK() OVER (PARTITION BY r.module, m.metric_name ORDER BY AVG(m.value)) AS low_value_rank FROM runs r JOIN metrics m ON r.id=m.run_id GROUP BY r.module, r.algorithm, m.metric_name ORDER BY r.module, m.metric_name, low_value_rank")]

    def save_snapshot(self, snapshot: dict[str, Any]) -> int:
        with self.connect() as conn:
            return int(conn.execute("INSERT INTO snapshots(taken_at, source, process_json) VALUES (?, ?, ?)", (snapshot["taken_at"], snapshot["source"], json.dumps(snapshot["processes"]))).lastrowid)
