from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class Question(Base):
    """
    雅思口语题目表。
    """

    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    part = Column(String(20), nullable=False)
    topic = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)


class PracticeRecord(Base):
    """
    练习记录表。
    """

    __tablename__ = "practice_records"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, nullable=False)
    answer = Column(Text, nullable=False)
    score = Column(String(20), nullable=False)
    feedback = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)


class PracticeSession(Base):
    """
    练习会话表。
    """

    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True, index=True)
    mode = Column(String(20), nullable=False, default="practice")
    part = Column(Integer, nullable=False)
    topic = Column(String(100), nullable=False)
    status = Column(String(20), nullable=False, default="active")
    feedback_json = Column(Text, nullable=True)
    started_at = Column(DateTime, default=datetime.now, nullable=False)
    finished_at = Column(DateTime, nullable=True)


class PracticeMessage(Base):
    """
    练习问答轮次表。
    """

    __tablename__ = "practice_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False)
    round_index = Column(Integer, nullable=False)
    part = Column(Integer, nullable=False)
    examiner_question = Column(Text, nullable=False)
    candidate_answer = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)


class ExamSession(Base):
    """
    考试会话表。
    """

    __tablename__ = "exam_sessions"

    id = Column(Integer, primary_key=True, index=True)
    question_id = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="ongoing")
    overall_score = Column(String(20), nullable=True)
    fluency_score = Column(String(20), nullable=True)
    lexical_score = Column(String(20), nullable=True)
    grammar_score = Column(String(20), nullable=True)
    feedback = Column(Text, nullable=True)
    suggestions = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    finished_at = Column(DateTime, nullable=True)


class ExamMessage(Base):
    """
    考试问答记录表。
    """

    __tablename__ = "exam_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, nullable=False)
    round_index = Column(Integer, nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
