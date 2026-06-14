from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessError
from app.schemas import (
    AnswerPracticeSessionRequest,
    AnswerPracticeSessionResponse,
    FinishPracticeSessionRequest,
    FinishPracticeSessionResponse,
    PracticeRecordResponse,
    StartPracticeSessionRequest,
    StartPracticeSessionResponse,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
)
from app.services.practice_service import (
    finish_practice_session,
    list_practice_records,
    start_practice_session,
    submit_answer,
    submit_practice_session_answer,
)


router = APIRouter(prefix="/practice", tags=["练习"])


@router.post("/sessions", response_model=StartPracticeSessionResponse)
def start_practice(
    request: StartPracticeSessionRequest,
    db: Session = Depends(get_db),
):
    """
    开始一次练习模式会话。
    """
    try:
        session, first_message = start_practice_session(
            db=db,
            part=request.part,
            topic=request.topic,
        )
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=error.message)

    return StartPracticeSessionResponse(
        session_id=session.id,
        mode=session.mode,
        part=session.part,
        topic=session.topic,
        status=session.status,
        current_question=first_message.examiner_question,
        round_index=first_message.round_index,
    )


@router.post(
    "/sessions/{session_id}/answer",
    response_model=AnswerPracticeSessionResponse,
)
def answer_practice(
    session_id: int,
    request: AnswerPracticeSessionRequest,
    db: Session = Depends(get_db),
):
    """
    提交练习回答并获取下一句考官追问。
    """
    try:
        session, next_message = submit_practice_session_answer(
            db=db,
            session_id=session_id,
            answer=request.answer,
        )
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=error.message)

    return AnswerPracticeSessionResponse(
        session_id=session.id,
        part=session.part,
        topic=session.topic,
        status=session.status,
        round_index=next_message.round_index,
        next_question=next_message.examiner_question,
    )


@router.post(
    "/sessions/{session_id}/finish",
    response_model=FinishPracticeSessionResponse,
)
def finish_practice(
    session_id: int,
    request: FinishPracticeSessionRequest | None = None,
    db: Session = Depends(get_db),
):
    """
    结束练习会话并获取练习评价。
    """
    try:
        session, feedback = finish_practice_session(
            db=db,
            session_id=session_id,
            final_answer=request.answer if request else None,
        )
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=error.message)

    return FinishPracticeSessionResponse(
        session_id=session.id,
        part=session.part,
        topic=session.topic,
        status=session.status,
        overall_score=feedback["overall_score"],
        fluency_feedback=feedback["fluency_feedback"],
        lexical_feedback=feedback["lexical_feedback"],
        grammar_feedback=feedback["grammar_feedback"],
        suggestions=feedback["suggestions"],
        improved_sample_answer=feedback["improved_sample_answer"],
    )


@router.post("/submit", response_model=SubmitAnswerResponse)
def submit_practice_answer(
    request: SubmitAnswerRequest,
    db: Session = Depends(get_db),
):
    """
    提交一次口语练习回答，返回模拟评分和建议。
    """
    try:
        record = submit_answer(
            db=db,
            question_id=request.question_id,
            answer=request.answer,
        )
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=error.message)

    return SubmitAnswerResponse(
        question_id=record.question_id,
        answer=record.answer,
        score=record.score,
        feedback=record.feedback,
    )


@router.get("/records", response_model=list[PracticeRecordResponse])
def get_practice_records(db: Session = Depends(get_db)):
    """
    查询历史练习记录。
    """
    return list_practice_records(db)
