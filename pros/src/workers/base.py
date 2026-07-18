"""Base worker class."""

import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from pros.src.utils import utcnow


class BaseWorker(ABC):
    """Base class for background workers."""
    
    def __init__(self, interval_minutes: int = 5):
        self.interval_minutes = interval_minutes
        self.running = False
        self.last_run: Optional[datetime] = None
        self.task: Optional[asyncio.Task] = None
    
    @abstractmethod
    async def run_once(self):
        """Run the worker once."""
        pass
    
    async def start(self):
        """Start the worker."""
        self.running = True
        self.task = asyncio.create_task(self._loop())
        print(f"Started worker: {self.__class__.__name__}")
    
    async def stop(self):
        """Stop the worker."""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        print(f"Stopped worker: {self.__class__.__name__}")
    
    async def _loop(self):
        """Main worker loop."""
        while self.running:
            try:
                await self.run_once()
                self.last_run = utcnow()
            except Exception as e:
                print(f"Worker {self.__class__.__name__} error: {e}")
            
            # Wait for next interval
            await asyncio.sleep(self.interval_minutes * 60)
    
    def should_run(self) -> bool:
        """Check if worker should run based on interval."""
        if not self.last_run:
            return True
        
        elapsed = utcnow() - self.last_run
        return elapsed >= timedelta(minutes=self.interval_minutes)
