from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base, get_db
from app.main import app
from app.services.question_service import init_default_questions


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


def test_finish_practice_with_current_answer(monkeypatch, tmp_path):
    from app.services import practice_service

    monkeypatch.setattr(practice_service, "call_chat_completion", lambda **kwargs: None)

    db_path = tmp_path / "practice.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    testing_session_local = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
    )
    Base.metadata.create_all(bind=engine)

    db = testing_session_local()
    try:
        init_default_questions(db)
    finally:
        db.close()

    def override_get_db():
        db = testing_session_local()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        test_client = TestClient(app)

        start_response = test_client.post(
            "/practice/sessions",
            json={
                "part": 1,
                "topic": "Work or Study",
            },
        )
        assert start_response.status_code == 200

        session_id = start_response.json()["session_id"]
        finish_response = test_client.post(
            f"/practice/sessions/{session_id}/finish",
            json={
                "answer": "I am a student, and I am preparing for IELTS because I want to study abroad.",
            },
        )

        assert finish_response.status_code == 200
        data = finish_response.json()
        assert data["status"] == "finished"
        assert data["overall_score"]
        assert data["improved_sample_answer"]

        second_start_response = test_client.post(
            "/practice/sessions",
            json={
                "part": 1,
                "topic": "Work or Study",
            },
        )
        assert second_start_response.status_code == 200

        second_session_id = second_start_response.json()["session_id"]
        answer_response = test_client.post(
            f"/practice/sessions/{second_session_id}/answer",
            json={
                "answer": "I am a student, and I usually spend my evenings improving my English speaking.",
            },
        )
        assert answer_response.status_code == 200

        second_finish_response = test_client.post(
            f"/practice/sessions/{second_session_id}/finish"
        )
        assert second_finish_response.status_code == 200
    finally:
        app.dependency_overrides.clear()
