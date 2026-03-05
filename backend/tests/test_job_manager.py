from backend.app.job_manager import JobManager
from backend.app.schemas import JobStatus


def test_single_active_job_per_user() -> None:
    manager = JobManager()
    job = manager.create_job("u1", 2025, "a.xlsx", "b.xls")
    assert job.status == JobStatus.queued

    try:
        manager.create_job("u1", 2025, "c.xlsx", "d.xls")
        assert False, "Deveria falhar ao criar segundo job ativo"
    except ValueError:
        assert True
