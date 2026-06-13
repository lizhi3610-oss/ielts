from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas import QuestionResponse
from app.services.question_service import list_questions


router = APIRouter(prefix="/questions", tags=["题库"])


@router.get("", response_model=list[QuestionResponse])
def get_questions(db: Session = Depends(get_db)):
    """
    查询雅思口语题库列表。
    """
    return list_questions(db)
