from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .database import RunStore
from .kernel import Kernel
from .probes import FakeProbe, PsutilProbe, stamped_snapshot

app = FastAPI(title="KernelLab", version="1.0.0")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
store, kernel = RunStore(os.getenv("KERNELLAB_DB", "data/kernellab.db")), Kernel()


class RunRequest(BaseModel):
    module: str
    algorithm: str
    params: dict[str, Any] = Field(default_factory=dict)
    seed: int | None = None


class SnapshotImport(BaseModel):
    taken_at: str
    source: str
    processes: list[dict[str, Any]]


@app.get("/")
def dashboard() -> FileResponse: return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.post("/run")
def run(request: RunRequest) -> dict[str, Any]:
    try:
        result = kernel.run(request.module, request.algorithm, request.params)
        run_id = store.save(request.module, request.params, result, request.seed)
        return {"run_id": run_id, **result.serializable()}
    except (KeyError, TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/history")
def history(module: str | None = None, algorithm: str | None = None, limit: int = Query(50, ge=1, le=250)) -> list[dict[str, Any]]:
    return store.history(module, algorithm, limit)


@app.get("/compare")
def compare(module: str, metric: str = "avg_waiting_time", workload_id: int | None = None) -> list[dict[str, Any]]:
    return store.compare(module, metric, workload_id)


@app.get("/stats")
def stats() -> list[dict[str, Any]]: return store.stats()


@app.post("/snapshots/import")
def import_snapshot(snapshot: SnapshotImport) -> dict[str, Any]:
    """Persist a Windows-host snapshot uploaded from outside the Linux container."""
    captured = snapshot.model_dump()
    return {"snapshot_id": store.save_snapshot(captured), "process_count": len(snapshot.processes), **captured}


@app.post("/snapshots/{source}")
def snapshot(source: str) -> dict[str, Any]:
    if source == "psutil": probe = PsutilProbe()
    elif source == "fake": probe = FakeProbe()
    else: raise HTTPException(status_code=422, detail="source must be fake or psutil")
    captured = stamped_snapshot(probe)
    return {"snapshot_id": store.save_snapshot(captured), **captured}
