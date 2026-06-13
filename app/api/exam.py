from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import BusinessError
from app.schemas import (
    AnswerExamRequest,
    AnswerExamResponse,
    FinishExamResponse,
    StartExamRequest,
    StartExamResponse,
)
from app.services.exam_service import finish_exam, start_exam, submit_exam_answer


router = APIRouter(prefix="/exam", tags=["考试"])


@router.post("/start", response_model=StartExamResponse)
def start_exam_session(
    request: StartExamRequest,
    db: Session = Depends(get_db),
):
    """
    开始一次雅思口语模拟考试。
    """
    try:
        session, current_question = start_exam(
            db=db,
            question_id=request.question_id,
        )
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=error.message)

    return StartExamResponse(
        session_id=session.id,
        current_question=current_question,
        round_index=1,
    )


@router.post("/answer", response_model=AnswerExamResponse)
def answer_exam_question(
    request: AnswerExamRequest,
    db: Session = Depends(get_db),
):
    """
    提交考试回答，返回下一轮追问或结束标志。
    """
    try:
        round_index, next_question, is_finished = submit_exam_answer(
            db=db,
            session_id=request.session_id,
            answer=request.answer,
        )
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=error.message)

    return AnswerExamResponse(
        session_id=request.session_id,
        round_index=round_index,
        next_question=next_question,
        is_finished=is_finished,
    )


@router.post("/finish", response_model=FinishExamResponse)
def finish_exam_session(
    session_id: int,
    db: Session = Depends(get_db),
):
    """
    结束考试并获取评分报告。
    """
    try:
        scores = finish_exam(db=db, session_id=session_id)
    except BusinessError as error:
        raise HTTPException(status_code=400, detail=error.message)

    return FinishExamResponse(
        overall_score=scores["overall_score"],
        fluency_score=scores["fluency_score"],
        lexical_score=scores["lexical_score"],
        grammar_score=scores["grammar_score"],
        feedback=scores["feedback"],
        suggestions=scores["suggestions"],
    )
