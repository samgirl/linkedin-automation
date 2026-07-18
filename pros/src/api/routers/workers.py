"""Worker management API routes."""

from fastapi import APIRouter, HTTPException
from typing import Optional

from pros.src.workers.event_processor import EventProcessorWorker
from pros.src.workers.memory_consolidator import MemoryConsolidatorWorker
from pros.src.workers.opportunity_scanner import OpportunityScannerWorker

router = APIRouter(prefix="/api/workers", tags=["workers"])

# Worker instances
_workers = {
    "event_processor": EventProcessorWorker(),
    "memory_consolidator": MemoryConsolidatorWorker(),
    "opportunity_scanner": OpportunityScannerWorker(),
}


@router.get("/")
async def list_workers():
    """List all workers and their status."""
    return {
        name: {
            "running": worker.running,
            "last_run": worker.last_run.isoformat() if worker.last_run else None,
            "interval_minutes": worker.interval_minutes,
        }
        for name, worker in _workers.items()
    }


@router.post("/{worker_name}/start")
async def start_worker(worker_name: str):
    """Start a worker."""
    worker = _workers.get(worker_name)
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker {worker_name} not found")
    
    if worker.running:
        return {"message": f"Worker {worker_name} is already running"}
    
    await worker.start()
    return {"message": f"Worker {worker_name} started"}


@router.post("/{worker_name}/stop")
async def stop_worker(worker_name: str):
    """Stop a worker."""
    worker = _workers.get(worker_name)
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker {worker_name} not found")
    
    if not worker.running:
        return {"message": f"Worker {worker_name} is not running"}
    
    await worker.stop()
    return {"message": f"Worker {worker_name} stopped"}


@router.post("/{worker_name}/run")
async def run_worker_once(worker_name: str):
    """Run a worker once immediately."""
    worker = _workers.get(worker_name)
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker {worker_name} not found")
    
    await worker.run_once()
    return {"message": f"Worker {worker_name} ran once"}


@router.post("/start-all")
async def start_all_workers():
    """Start all workers."""
    for worker in _workers.values():
        if not worker.running:
            await worker.start()
    return {"message": "All workers started"}


@router.post("/stop-all")
async def stop_all_workers():
    """Stop all workers."""
    for worker in _workers.values():
        if worker.running:
            await worker.stop()
    return {"message": "All workers stopped"}
