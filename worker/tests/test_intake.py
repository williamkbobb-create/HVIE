import io
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app


def image_bytes(color: tuple[int, int, int]) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 800), color=color).save(buffer, format="JPEG", quality=90)
    return buffer.getvalue()


def make_client(tmp_path):
    return TestClient(create_app(api_token="test-secret", storage_root=tmp_path))


def make_files():
    return [
        ("photos", (f"car-{i}.jpg", image_bytes((i * 17, i * 11, i * 7)), "image/jpeg"))
        for i in range(12)
    ]


def submit_job(client):
    response = client.post(
        "/v1/jobs",
        headers={"Authorization": "Bearer test-secret"},
        data={"project_name": "Toyota test", "vehicle_category": "Passenger car"},
        files=make_files(),
    )
    assert response.status_code == 202, response.text
    return response.json()["job_id"]


def test_health_and_authentication(tmp_path):
    client = make_client(tmp_path)
    assert client.get("/health").json()["mode"] == "private-queue-no-reconstruction"
    assert client.get("/v1/jobs/not-a-uuid").status_code == 401


def test_job_intake_and_manifest(tmp_path):
    client = make_client(tmp_path)
    job_id = submit_job(client)
    manifest = client.get(f"/v1/jobs/{job_id}", headers={"Authorization": "Bearer test-secret"})
    assert manifest.status_code == 200
    assert manifest.json()["status"] == "queued"
    assert len(manifest.json()["photos"]) == 12
    assert manifest.json()["queue"]["attempt_count"] == 0


def test_rejects_duplicate_images_and_cleans_staging(tmp_path):
    client = make_client(tmp_path)
    duplicate = image_bytes((1, 2, 3))
    files = [("photos", (f"same-{i}.jpg", duplicate, "image/jpeg")) for i in range(12)]
    response = client.post(
        "/v1/jobs",
        headers={"Authorization": "Bearer test-secret"},
        data={"project_name": "Duplicate test", "vehicle_category": "Car"},
        files=files,
    )
    assert response.status_code == 422
    assert not list(tmp_path.glob(".*-*"))


def test_claim_heartbeat_fail_and_retry(tmp_path):
    client = make_client(tmp_path)
    job_id = submit_job(client)
    headers = {"Authorization": "Bearer test-secret"}
    claim = client.post("/v1/worker/claim", headers=headers, json={"worker_id": "worker-test"})
    assert claim.status_code == 200
    lease = claim.json()
    assert lease["status"] == "claimed"
    assert lease["job_id"] == job_id
    identity = {"worker_id": "worker-test", "lease_token": lease["lease_token"]}

    heartbeat = client.post(f"/v1/worker/heartbeat?job_id={job_id}", headers=headers, json=identity)
    assert heartbeat.status_code == 200

    failed = client.post(f"/v1/worker/fail?job_id={job_id}", headers=headers, json={**identity, "error": "COLMAP not installed"})
    assert failed.status_code == 200
    assert failed.json()["status"] == "queued"
    manifest = client.get(f"/v1/jobs/{job_id}", headers=headers).json()
    assert manifest["queue"]["attempt_count"] == 1
    assert manifest["queue"]["last_error"] == "COLMAP not installed"


def test_worker_cannot_use_another_workers_lease(tmp_path):
    client = make_client(tmp_path)
    job_id = submit_job(client)
    headers = {"Authorization": "Bearer test-secret"}
    claim = client.post("/v1/worker/claim", headers=headers, json={"worker_id": "worker-one"}).json()
    bad = client.post(
        f"/v1/worker/heartbeat?job_id={job_id}",
        headers=headers,
        json={"worker_id": "worker-two", "lease_token": claim["lease_token"]},
    )
    assert bad.status_code == 409


def test_cancel_prevents_future_claim(tmp_path):
    client = make_client(tmp_path)
    job_id = submit_job(client)
    headers = {"Authorization": "Bearer test-secret"}
    cancelled = client.post(f"/v1/jobs/{job_id}/cancel", headers=headers, json={"reason": "operator stop"})
    assert cancelled.status_code == 200
    claim = client.post("/v1/worker/claim", headers=headers, json={"worker_id": "worker-test"})
    assert claim.json()["status"] == "idle"
    assert client.get(f"/v1/jobs/{job_id}", headers=headers).json()["status"] == "cancelled"


def test_empty_queue_returns_idle(tmp_path):
    client = make_client(tmp_path)
    response = client.post(
        "/v1/worker/claim",
        headers={"Authorization": "Bearer test-secret"},
        json={"worker_id": "worker-test"},
    )
    assert response.json()["status"] == "idle"


def test_expired_lease_is_reclaimed_and_old_worker_is_rejected(tmp_path):
    import sqlite3

    client = make_client(tmp_path)
    job_id = submit_job(client)
    headers = {"Authorization": "Bearer test-secret"}
    first = client.post(
        "/v1/worker/claim", headers=headers, json={"worker_id": "worker-one"}
    ).json()
    with sqlite3.connect(tmp_path / "queue.sqlite3") as db:
        db.execute(
            "UPDATE jobs SET lease_expires_at=? WHERE job_id=?",
            ("2000-01-01T00:00:00+00:00", job_id),
        )
        db.commit()

    second_response = client.post(
        "/v1/worker/claim", headers=headers, json={"worker_id": "worker-two"}
    )
    assert second_response.status_code == 200
    second = second_response.json()
    assert second["status"] == "claimed"
    assert second["job_id"] == job_id
    assert second["attempt"] == 2

    stale = client.post(
        f"/v1/worker/heartbeat?job_id={job_id}",
        headers=headers,
        json={"worker_id": "worker-one", "lease_token": first["lease_token"]},
    )
    assert stale.status_code == 409


def test_job_fails_after_maximum_attempts(tmp_path):
    client = make_client(tmp_path)
    job_id = submit_job(client)
    headers = {"Authorization": "Bearer test-secret"}
    for attempt in range(3):
        claim = client.post(
            "/v1/worker/claim",
            headers=headers,
            json={"worker_id": f"worker-{attempt}"},
        ).json()
        assert claim["status"] == "claimed"
        failed = client.post(
            f"/v1/worker/fail?job_id={job_id}",
            headers=headers,
            json={
                "worker_id": f"worker-{attempt}",
                "lease_token": claim["lease_token"],
                "error": f"failure {attempt + 1}",
            },
        )
        assert failed.status_code == 200
    state = client.get(f"/v1/jobs/{job_id}", headers=headers).json()
    assert state["status"] == "failed"
    assert state["queue"]["attempt_count"] == 3
    idle = client.post(
        "/v1/worker/claim", headers=headers, json={"worker_id": "worker-final"}
    ).json()
    assert idle["status"] == "idle"
