from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["agent_mode"] == "deterministic-tool-using"


def test_create_study_plan_returns_schedule_and_request_id() -> None:
    response = client.post(
        "/api/v1/agent/study-plan",
        headers={"X-Request-ID": "test-request-001"},
        json={
            "goal": "Học Python để xây dựng API backend",
            "weekly_hours": 6,
            "weeks": 2,
            "current_level": "beginner",
            "preferred_days": ["Mon", "Wed", "Fri"],
        },
    )
    body = response.json()
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "test-request-001"
    assert body["metadata"]["sessions"] == 6
    assert len(body["weekly_schedule"]) == 6
    assert body["weekly_schedule"][0]["duration_hours"] == 2.0


def test_invalid_payload_has_stable_error_shape() -> None:
    response = client.post(
        "/api/v1/agent/study-plan",
        json={"goal": "x", "weekly_hours": 0},
    )
    assert response.status_code == 422
    assert response.json() == {
        "error": {"code": "VALIDATION_ERROR", "message": "Dữ liệu đầu vào không hợp lệ."}
    }


def test_unknown_goal_uses_general_modules() -> None:
    response = client.post(
        "/api/v1/agent/study-plan",
        json={"goal": "Học một kỹ năng mới", "weekly_hours": 3, "weeks": 1},
    )
    assert response.status_code == 200
    assert response.json()["weekly_schedule"]
    assert response.json()["weekly_schedule"][0]["topic"] == "Khái niệm cốt lõi"

