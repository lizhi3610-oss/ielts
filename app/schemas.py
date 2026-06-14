from datetime import datetime

from pydantic import BaseModel, Field


class QuestionResponse(BaseModel):
    id: int
    part: str
    topic: str
    content: str

    model_config = {
        "from_attributes": True
    }


class SubmitAnswerRequest(BaseModel):
    question_id: int = Field(..., gt=0, description="题目 ID")
    answer: str = Field(..., min_length=1, description="用户的文本回答")


class SubmitAnswerResponse(BaseModel):
    question_id: int
    answer: str
    score: str
    feedback: str


class PracticeRecordResponse(BaseModel):
    id: int
    question_id: int
    answer: str
    score: str
    feedback: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }


class StartPracticeSessionRequest(BaseModel):
    part: int = Field(..., ge=1, le=3, description="IELTS Speaking Part")
    topic: str | None = Field(None, description="练习话题")


class StartPracticeSessionResponse(BaseModel):
    session_id: int
    mode: str
    part: int
    topic: str
    status: str
    current_question: str
    round_index: int


class AnswerPracticeSessionRequest(BaseModel):
    answer: str = Field(..., min_length=1, description="用户的文本回答")


class AnswerPracticeSessionResponse(BaseModel):
    session_id: int
    part: int
    topic: str
    status: str
    round_index: int
    next_question: str


class FinishPracticeSessionRequest(BaseModel):
    answer: str | None = Field(None, min_length=1, description="结束前的当前回答")


class FinishPracticeSessionResponse(BaseModel):
    session_id: int
    part: int
    topic: str
    status: str
    overall_score: str
    fluency_feedback: str
    lexical_feedback: str
    grammar_feedback: str
    suggestions: str
    improved_sample_answer: str


class StartExamRequest(BaseModel):
    question_id: int = Field(..., gt=0, description="题目 ID")


class StartExamResponse(BaseModel):
    session_id: int
    current_question: str
    round_index: int


class AnswerExamRequest(BaseModel):
    session_id: int = Field(..., gt=0, description="考试会话 ID")
    answer: str = Field(..., min_length=1, description="用户的文本回答")


class AnswerExamResponse(BaseModel):
    session_id: int
    round_index: int
    next_question: str | None
    is_finished: bool


class FinishExamResponse(BaseModel):
    overall_score: str
    fluency_score: str
    lexical_score: str
    grammar_score: str
    feedback: str
    suggestions: str
