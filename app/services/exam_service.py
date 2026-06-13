import random
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.models import ExamMessage, ExamSession, Question


def generate_follow_up_question(round_index: int, user_answer: str) -> str:
    """
    根据轮次和用户回答生成追问。

    v0.1 使用规则 Mock，不接大模型。
    """
    follow_ups = [
        "Can you give me a specific example to illustrate your point?",
        "Why do you think that is the case?",
        "How does this compare to the situation in your country?",
        "What are the advantages and disadvantages of this?",
        "Do you think this will change in the future?",
    ]

    return random.choice(follow_ups)


def generate_mock_scores() -> dict:
    """
    生成模拟评分。

    v0.1 使用随机分数模拟。
    """
    scores = ["5.5", "6.0", "6.5", "7.0", "7.5"]

    return {
        "overall_score": random.choice(scores),
        "fluency_score": random.choice(scores),
        "lexical_score": random.choice(scores),
        "grammar_score": random.choice(scores),
        "feedback": "Your answers show good understanding of the topics. You maintained coherence throughout the conversation.",
        "suggestions": "Try to use more varied vocabulary and complex sentence structures. Pay attention to verb tenses and article usage.",
    }


def start_exam(db: Session, question_id: int) -> tuple[ExamSession, str]:
    """
    开始一次考试会话。
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise BusinessError("题目不存在")

    session = ExamSession(
        question_id=question_id,
        status="ongoing",
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    first_message = ExamMessage(
        session_id=session.id,
        round_index=1,
        role="examiner",
        content=question.content,
    )

    db.add(first_message)
    db.commit()

    return session, question.content


def submit_exam_answer(db: Session, session_id: int, answer: str) -> tuple[int, str | None, bool]:
    """
    提交考试回答，返回 (round_index, next_question, is_finished)。
    """
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if session is None:
        raise BusinessError("考试会话不存在")

    if session.status != "ongoing":
        raise BusinessError("考试已结束")

    if not answer or not answer.strip():
        raise BusinessError("回答内容不能为空")

    current_round = db.query(ExamMessage).filter(
        ExamMessage.session_id == session_id
    ).count() // 2 + 1

    user_message = ExamMessage(
        session_id=session_id,
        round_index=current_round,
        role="user",
        content=answer.strip(),
    )

    db.add(user_message)
    db.commit()

    if current_round >= 3:
        return current_round, None, True

    next_question = generate_follow_up_question(current_round, answer)

    examiner_message = ExamMessage(
        session_id=session_id,
        round_index=current_round + 1,
        role="examiner",
        content=next_question,
    )

    db.add(examiner_message)
    db.commit()

    return current_round + 1, next_question, False


def finish_exam(db: Session, session_id: int) -> dict:
    """
    结束考试并生成评分报告。
    """
    session = db.query(ExamSession).filter(ExamSession.id == session_id).first()
    if session is None:
        raise BusinessError("考试会话不存在")

    if session.status == "finished":
        return {
            "overall_score": session.overall_score,
            "fluency_score": session.fluency_score,
            "lexical_score": session.lexical_score,
            "grammar_score": session.grammar_score,
            "feedback": session.feedback,
            "suggestions": session.suggestions,
        }

    scores = generate_mock_scores()

    session.status = "finished"
    session.overall_score = scores["overall_score"]
    session.fluency_score = scores["fluency_score"]
    session.lexical_score = scores["lexical_score"]
    session.grammar_score = scores["grammar_score"]
    session.feedback = scores["feedback"]
    session.suggestions = scores["suggestions"]
    session.finished_at = datetime.now()

    db.commit()

    return scores
