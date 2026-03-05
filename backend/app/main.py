from __future__ import annotations

import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router
from .config import settings
from .job_manager import JobManager
from .job_runner import JobRunner
from .realtime import RealtimeHub
from .storage import delete_job_dir


def create_app() -> FastAPI:
    app = FastAPI(title="Notas Compensadas API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    app.state.job_manager = JobManager()
    app.state.realtime = RealtimeHub()
    app.state.job_runner = JobRunner(app.state.job_manager, app.state.realtime)

    @app.on_event("startup")
    async def startup() -> None:
        app.state.realtime.set_loop(asyncio.get_running_loop())

        async def cleanup_task() -> None:
            while True:
                await asyncio.sleep(settings.cleanup_interval_seconds)
                expired_jobs = app.state.job_manager.expire_jobs(settings.ttl_seconds)
                for job in expired_jobs:
                    delete_job_dir(job.job_dir)
                    app.state.realtime.status(job.job_id, "expired")

        app.state.cleanup_task = asyncio.create_task(cleanup_task())

    @app.on_event("shutdown")
    async def shutdown() -> None:
        cleanup_task = getattr(app.state, "cleanup_task", None)
        if cleanup_task:
            cleanup_task.cancel()

    return app


app = create_app()
