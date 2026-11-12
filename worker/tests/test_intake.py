import io
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app


def image_bytes(color: tuple[int, int, int] = (255, 0, 0)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (1200, 800), color=color).save(buffer, format="JPEG")
    return buffer.getvalue()


def make_client(tmp_path):
    return TestClient(create_app(api_token="test-secret", storage_root=tmp_path))


def test_health_is_public_and_does_not_expose_storage(tmp_path):
    response = make_client(tmp_path).get("/health")
    assert response.status_code == 200
    assert response.json()["mode"] == "intake-only"
    assert str(tmp_path) not in response.text


def test_job_requires_bearer_token(tmp_path):
    response = make_client(tmp_path).post("/v1/jobs", data={
        "project_name": "Car project", "vehicle_category": "Passenger car"
    })
    assert response.status_code == 401


def test_accepts_images_and_writes_private_manifest(tmp_path):
    client = make_client(tmp_path)
    files = [("photos", (f"car-{i}.jpg", image_bytes((i * 17, i * 11, i * 7)), "image/jpeg")) for i in range(12)]
    response = client.post(
        "/v1/jobs",
        headers={"Authorization": "Bearer test-secret"},
        data={"project_name": "Toyota test", "vehicle_category": "Passenger car"},
        files=files,
    )
    assert response.status_code == 202, response.text
    result = response.json()
    assert result["photo_count"] == 12
    job_id = result["job_id"]
    assert (tmp_path / job_id / "manifest.json").is_file()
    manifest = client.get(f"/v1/jobs/{job_id}", headers={"Authorization": "Bearer test-secret"})
    assert manifest.status_code == 200
    assert manifest.json()["processing"]["reconstruction_started"] is False


def test_rejects_duplicate_images_and_cleans_staging(tmp_path):
    client = make_client(tmp_path)
    duplicate = image_bytes()
    files = [("photos", (f"same-{i}.jpg", duplicate, "image/jpeg")) for i in range(12)]
    response = client.post(
        "/v1/jobs",
        headers={"Authorization": "Bearer test-secret"},
        data={"project_name": "Duplicate test", "vehicle_category": "Car"},
        files=files,
    )
    assert response.status_code == 422
    assert list(tmp_path.iterdir()) == []


def test_rejects_invalid_job_identifier(tmp_path):
    response = make_client(tmp_path).get(
        "/v1/jobs/../../etc/passwd",
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 404
