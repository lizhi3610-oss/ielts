from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_list_questions():
    response = client.get("/questions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_submit_answer_with_invalid_question():
    response = client.post(
        "/practice/submit",
        json={
            "question_id": 999999,
            "answer": "This is a test answer.",
        },
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "题目不存在"
