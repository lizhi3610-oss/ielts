import json
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import BusinessError
from app.models import PracticeMessage, PracticeRecord, PracticeSession, Question
from app.services.llm_service import call_chat_completion


PRACTICE_FALLBACK_QUESTIONS = {
    1: "Can you tell me more about that?",
    2: "What made this experience memorable for you?",
    3: "Why do you think this issue matters in modern society?",
}

PRACTICE_FALLBACK_TOPICS = {
    1: "Work or Study",
    2: "Person",
    3: "Technology",
}

PRACTICE_FALLBACK_FIRST_QUESTIONS = {
    1: "Do you work or are you a student?",
    2: "Describe a person who inspired you.",
    3: "How has technology changed the way people communicate?",
}

INCOMPLETE_QUESTION_ENDINGS = (
    " a?",
    " an?",
    " the?",
    " of?",
    " to?",
    " for?",
    " with?",
    " about?",
    " in?",
    " on?",
    " at?",
    " by?",
    " from?",
    " and?",
    " or?",
    " my?",
    " your?",
    " his?",
    " her?",
    " their?",
    " our?",
    " approach?",
    " solve?",
    " build?",
    " use?",
    " improve?",
    " affect?",
    " handle?",
    " manage?",
    " develop?",
    " deal?",
)

GENERIC_FOLLOW_UPS = {
    "Can you tell me more about that?",
    "Can you give me an example?",
    "What do you usually do?",
}


def generate_mock_feedback(answer: str) -> tuple[str, str]:
    """
    生成模拟评分反馈。

    v0.1 先不用真实大模型，而是用简单规则模拟。
    这样你可以优先练接口、数据库、异常处理这些工程基本功。
    """
    clean_answer = answer.strip()
    word_count = len(clean_answer.split())

    if word_count < 20:
        return (
            "5.0",
            "你的回答偏短，信息量不足。建议补充原因、例子和个人感受，让回答更完整。",
        )

    if word_count < 50:
        return (
            "6.0",
            "你的回答基本完整，但表达还可以更自然。建议增加连接词，并使用更丰富的词汇。",
        )

    return (
        "7.0",
        "你的回答内容较完整，逻辑比较清楚。下一步可以优化语法准确性和表达多样性。",
    )


def submit_answer(db: Session, question_id: int, answer: str) -> PracticeRecord:
    """
    提交练习回答并保存记录。
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise BusinessError("题目不存在")

    if not answer or not answer.strip():
        raise BusinessError("回答内容不能为空")

    score, feedback = generate_mock_feedback(answer)

    record = PracticeRecord(
        question_id=question_id,
        answer=answer.strip(),
        score=score,
        feedback=feedback,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def list_practice_records(db: Session) -> list[PracticeRecord]:
    """
    查询历史练习记录。
    """
    return db.query(PracticeRecord).order_by(PracticeRecord.id.desc()).all()


def normalize_question(text: str | None) -> str | None:
    """
    将 LLM 输出收敛成一个英文问题。
    """
    if not text:
        return None

    clean_text = text.strip().strip('"').strip("'")
    clean_text = clean_text.splitlines()[0].strip()
    if not clean_text:
        return None

    if "." in clean_text and "?" in clean_text:
        clean_text = clean_text[: clean_text.find("?") + 1]

    if not clean_text.endswith("?"):
        clean_text = f"{clean_text.rstrip('.')}?"

    if not is_usable_follow_up_question(clean_text):
        return None

    return clean_text


def is_usable_follow_up_question(question: str) -> bool:
    """
    判断追问是否足够完整、自然。
    """
    clean_question = question.strip()
    if not clean_question.endswith("?"):
        return False

    if clean_question in GENERIC_FOLLOW_UPS:
        return False

    words = clean_question.split()
    if len(words) < 5 or len(words) > 28:
        return False

    if clean_question.endswith(INCOMPLETE_QUESTION_ENDINGS):
        return False

    lower_question = clean_question.lower()
    if lower_question.startswith("how do you usually approach "):
        tail = clean_question[:-1].split()[5:]
        if len(tail) <= 1:
            return False

    return True


def choose_non_repeating_question(
    candidates: list[str],
    previous_questions: list[str],
) -> str:
    """
    从候选追问里选择一个未重复且可用的问题。
    """
    previous_set = {question.strip().lower() for question in previous_questions}

    for candidate in candidates:
        clean_candidate = candidate.strip()
        if (
            clean_candidate.lower() not in previous_set
            and is_usable_follow_up_question(clean_candidate)
        ):
            return clean_candidate

    return "Could you give me a little more detail about your answer?"


def generate_fallback_follow_up(
    part: int,
    topic: str,
    examiner_question: str,
    answer: str,
    previous_questions: list[str] | None = None,
) -> str:
    """
    本地生成更自然的追问，避免直接复读用户回答。
    """
    clean_answer = answer.strip().lower()
    words = clean_answer.split()
    has_letters = any(char.isalpha() for char in clean_answer)
    clean_topic = topic.lower()
    clean_examiner_question = examiner_question.lower()
    previous_questions = previous_questions or []

    if not has_letters or len(words) <= 2:
        return choose_non_repeating_question(
            [
                "Could you give me a little more detail about your answer?",
                "Can you expand on that with one example?",
                "What is the main reason for your answer?",
            ],
            previous_questions,
        )

    if part == 1:
        if clean_topic == "work or study":
            if any(keyword in clean_answer for keyword in ["student", "study", "major", "university"]):
                return choose_non_repeating_question(
                    [
                        "What do you enjoy most about your studies?",
                        "What subject do you find most challenging?",
                        "How do you think your studies will help you in the future?",
                    ],
                    previous_questions,
                )
            if any(keyword in clean_answer for keyword in ["work", "job", "internship", "developer", "company"]):
                return choose_non_repeating_question(
                    [
                        "What skill have you learned from this work?",
                        "What part of this work is most challenging for you?",
                        "How could this experience help your future career?",
                    ],
                    previous_questions,
                )
            return choose_non_repeating_question(
                [
                    "Why did you choose this path?",
                    "What do you like most about it?",
                    "Would you like to continue doing this in the future?",
                ],
                previous_questions,
            )

        if clean_topic == "hometown":
            if any(keyword in clean_answer for keyword in ["history", "historical", "old", "traditional"]):
                return choose_non_repeating_question(
                    [
                        "What historical place in your hometown would you recommend?",
                        "How does this history affect local life today?",
                        "Do many young people in your hometown care about its history?",
                    ],
                    previous_questions,
                )
            return choose_non_repeating_question(
                [
                    "What do you like most about your hometown?",
                    "How has your hometown changed in recent years?",
                    "Would you like to live in your hometown in the future?",
                ],
                previous_questions,
            )

        if clean_topic == "daily routine":
            if any(keyword in clean_answer for keyword in ["weekend", "morning", "afternoon", "routine"]):
                return choose_non_repeating_question(
                    [
                        "Why do you like spending your time in that way?",
                        "How is your weekend different from your weekdays?",
                        "Would you like to change your weekend routine?",
                    ],
                    previous_questions,
                )
            return choose_non_repeating_question(
                [
                    "How is your weekend different from your weekdays?",
                    "What do you usually do to relax?",
                    "Do you prefer planning your weekend or keeping it flexible?",
                ],
                previous_questions,
            )

    if part == 2:
        if clean_topic == "person":
            if any(keyword in clean_answer for keyword in ["father", "mother", "teacher", "classmate", "friend", "he", "she"]):
                return choose_non_repeating_question(
                    [
                        "What quality of this person do you admire most?",
                        "How did this person influence your life?",
                        "Can you describe one specific thing this person did?",
                    ],
                    previous_questions,
                )
            return choose_non_repeating_question(
                [
                    "How did this person influence your life?",
                    "When did you first meet or learn about this person?",
                    "Why do you still remember this person?",
                ],
                previous_questions,
            )

        if clean_topic == "place":
            if any(keyword in clean_answer for keyword in ["quiet", "library", "calm", "peaceful"]):
                return choose_non_repeating_question(
                    [
                        "Why is a quiet atmosphere important to you?",
                        "How do you usually spend your time there?",
                        "Would you recommend this place to your friends?",
                    ],
                    previous_questions,
                )
            return choose_non_repeating_question(
                [
                    "What did you enjoy most about this place?",
                    "Who would you like to visit this place with?",
                    "How did you feel when you were there?",
                ],
                previous_questions,
            )

        return choose_non_repeating_question(
            [
                "What made this experience especially memorable for you?",
                "How did you feel at that time?",
                "Would you like to have a similar experience again?",
            ],
            previous_questions,
        )

    if part == 3:
        if "communicat" in clean_examiner_question:
            if any(keyword in clean_answer for keyword in ["faster", "instant", "message", "online", "remote", "country"]):
                return choose_non_repeating_question(
                    [
                        "Do you think faster communication always improves relationships?",
                        "What problems can instant communication create?",
                        "How has online communication changed family relationships?",
                    ],
                    previous_questions,
                )
            if any(keyword in clean_answer for keyword in ["education", "school", "student", "teacher"]):
                return choose_non_repeating_question(
                    [
                        "How could this technology affect communication between students and teachers?",
                        "Do you think technology makes classroom communication more effective?",
                        "What risks could appear if students rely too much on technology?",
                    ],
                    previous_questions,
                )
            return choose_non_repeating_question(
                [
                    "Can you give a specific example of how technology changes communication?",
                    "Do you think people communicate better now than in the past?",
                    "What kind of technology has had the biggest impact on communication?",
                ],
                previous_questions,
            )

        if "future" in clean_answer or "society" in clean_answer:
            return choose_non_repeating_question(
                [
                    "What specific change do you think will have the biggest impact?",
                    "How should people prepare for that change?",
                    "Who will benefit most from this change?",
                ],
                previous_questions,
            )

        return choose_non_repeating_question(
            [
                "Why do you think this topic is important in modern society?",
                "What are the main advantages and disadvantages of this trend?",
                "How might this situation change in the future?",
            ],
            previous_questions,
        )

    return choose_non_repeating_question(
        [
            PRACTICE_FALLBACK_QUESTIONS.get(part, "Can you tell me more about that?"),
            "Can you expand on that with one example?",
            "What is the main reason for your answer?",
        ],
        previous_questions,
    )


def generate_practice_follow_up(
    part: int,
    topic: str,
    examiner_question: str,
    answer: str,
    previous_questions: list[str] | None = None,
) -> str:
    """
    基于用户回答生成下一句考官追问。
    """
    messages = [
        {
            "role": "system",
            "content": (
                "You are an IELTS Speaking examiner. "
                "Ask exactly one concise English follow-up question. "
                "The question must be directly related to the candidate's answer. "
                "If the answer is short, ask a simple clarification question. "
                "Do not repeat the candidate's exact wording. "
                "Do not give feedback, scores, explanations, or multiple questions."
            ),
        },
        {
            "role": "user",
            "content": (
                f"IELTS Speaking Part: {part}\n"
                f"Topic: {topic}\n"
                f"Previous examiner question: {examiner_question}\n"
                f"Candidate answer: {answer}\n"
                "Return one English follow-up question only."
            ),
        },
    ]
    llm_question = normalize_question(
        call_chat_completion(messages=messages, max_tokens=80, temperature=0.5)
    )
    previous_questions = previous_questions or []
    previous_set = {question.strip().lower() for question in previous_questions}
    if llm_question and llm_question.strip().lower() not in previous_set:
        return llm_question

    return generate_fallback_follow_up(
        part=part,
        topic=topic,
        examiner_question=examiner_question,
        answer=answer,
        previous_questions=previous_questions,
    )


def build_fallback_feedback(
    part: int,
    topic: str,
    answered_messages: list[PracticeMessage],
) -> dict[str, str]:
    """
    本地生成练习评价，保证 LLM 不可用时接口仍可用。
    """
    answers = [
        message.candidate_answer or ""
        for message in answered_messages
        if message.candidate_answer
    ]
    word_count = len(" ".join(answers).split())

    if word_count < 30:
        score = "5.5"
        fluency = "Your answers are understandable but quite short. Try to extend each answer with reasons and examples."
    elif word_count < 80:
        score = "6.0"
        fluency = "You can keep the conversation going, but some answers need smoother development and clearer linking."
    else:
        score = "6.5"
        fluency = "You provide enough information and generally maintain the flow of the conversation."

    return {
        "overall_score": score,
        "fluency_feedback": fluency,
        "lexical_feedback": "Use more specific topic vocabulary and avoid repeating the same simple words.",
        "grammar_feedback": "Focus on accurate verb forms, articles, and longer complex sentences.",
        "suggestions": "Answer directly, add one clear reason, and support it with a short personal example.",
        "improved_sample_answer": (
            f"For this {topic} question in Part {part}, I would give a direct answer first, "
            "then add a reason and a concrete example to make the response more natural and complete."
        ),
    }


def parse_feedback_json(content: str | None) -> dict[str, str] | None:
    """
    解析并校验 LLM 评价 JSON。
    """
    if not content:
        return None

    clean_content = content.strip()
    if clean_content.startswith("```"):
        clean_content = clean_content.strip("`")
        clean_content = clean_content.replace("json", "", 1).strip()

    try:
        data = json.loads(clean_content)
    except json.JSONDecodeError:
        return None

    required_fields = [
        "overall_score",
        "fluency_feedback",
        "lexical_feedback",
        "grammar_feedback",
        "suggestions",
        "improved_sample_answer",
    ]
    if not all(isinstance(data.get(field), str) for field in required_fields):
        return None

    return {field: data[field] for field in required_fields}


def generate_practice_feedback(
    session: PracticeSession,
    answered_messages: list[PracticeMessage],
) -> dict[str, str]:
    """
    生成练习评价。
    """
    transcript = "\n".join(
        [
            (
                f"Examiner: {message.examiner_question}\n"
                f"Candidate: {message.candidate_answer}"
            )
            for message in answered_messages
            if message.candidate_answer
        ]
    )

    messages = [
        {
            "role": "system",
            "content": (
                "You are an IELTS Speaking coach. Evaluate the candidate's practice answers. "
                "Return valid JSON only."
            ),
        },
        {
            "role": "user",
            "content": (
                f"IELTS Speaking Part: {session.part}\n"
                f"Topic: {session.topic}\n"
                f"Transcript:\n{transcript}\n\n"
                "Return JSON with these string fields only: "
                "overall_score, fluency_feedback, lexical_feedback, grammar_feedback, "
                "suggestions, improved_sample_answer."
            ),
        },
    ]

    feedback = parse_feedback_json(
        call_chat_completion(messages=messages, max_tokens=700, temperature=0.3)
    )
    if feedback:
        return feedback

    return build_fallback_feedback(
        part=session.part,
        topic=session.topic,
        answered_messages=answered_messages,
    )


def get_default_question(db: Session, part: int, topic: str | None) -> Question | None:
    """
    根据 part 和 topic 获取默认练习题。
    """
    query = db.query(Question).filter(Question.part == f"Part {part}")
    if topic:
        topic_question = query.filter(Question.topic == topic.strip()).first()
        if topic_question:
            return topic_question

    return query.order_by(Question.id.asc()).first()


def start_practice_session(
    db: Session,
    part: int,
    topic: str | None = None,
) -> tuple[PracticeSession, PracticeMessage]:
    """
    开始一次练习会话。
    """
    if part not in (1, 2, 3):
        raise BusinessError("练习 Part 不合法")

    question = get_default_question(db=db, part=part, topic=topic)
    session_topic = (
        topic.strip()
        if topic and topic.strip()
        else question.topic
        if question is not None
        else PRACTICE_FALLBACK_TOPICS[part]
    )
    first_question = (
        question.content
        if question is not None
        else PRACTICE_FALLBACK_FIRST_QUESTIONS[part]
    )

    session = PracticeSession(
        mode="practice",
        part=part,
        topic=session_topic,
        status="active",
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    first_message = PracticeMessage(
        session_id=session.id,
        round_index=1,
        part=part,
        examiner_question=first_question,
    )
    db.add(first_message)
    db.commit()
    db.refresh(first_message)

    return session, first_message


def submit_practice_session_answer(
    db: Session,
    session_id: int,
    answer: str,
) -> tuple[PracticeSession, PracticeMessage]:
    """
    提交练习回答并生成下一句追问。
    """
    session = db.query(PracticeSession).filter(PracticeSession.id == session_id).first()
    if session is None:
        raise BusinessError("练习会话不存在")

    if session.status != "active":
        raise BusinessError("练习会话已结束")

    if not answer or not answer.strip():
        raise BusinessError("回答内容不能为空")

    current_message = (
        db.query(PracticeMessage)
        .filter(
            PracticeMessage.session_id == session_id,
            PracticeMessage.candidate_answer.is_(None),
        )
        .order_by(PracticeMessage.round_index.desc())
        .first()
    )
    if current_message is None:
        raise BusinessError("当前练习问题不存在")

    current_message.candidate_answer = answer.strip()
    previous_questions = [
        message.examiner_question
        for message in (
            db.query(PracticeMessage)
            .filter(PracticeMessage.session_id == session_id)
            .order_by(PracticeMessage.round_index.asc())
            .all()
        )
    ]

    next_question = generate_practice_follow_up(
        part=session.part,
        topic=session.topic,
        examiner_question=current_message.examiner_question,
        answer=answer.strip(),
        previous_questions=previous_questions,
    )
    next_message = PracticeMessage(
        session_id=session.id,
        round_index=current_message.round_index + 1,
        part=session.part,
        examiner_question=next_question,
    )

    db.add(next_message)
    db.commit()
    db.refresh(next_message)

    return session, next_message


def finish_practice_session(db: Session, session_id: int) -> tuple[PracticeSession, dict[str, str]]:
    """
    结束练习会话并生成评价。
    """
    session = db.query(PracticeSession).filter(PracticeSession.id == session_id).first()
    if session is None:
        raise BusinessError("练习会话不存在")

    if session.status == "finished" and session.feedback_json:
        return session, json.loads(session.feedback_json)

    answered_messages = (
        db.query(PracticeMessage)
        .filter(
            PracticeMessage.session_id == session_id,
            PracticeMessage.candidate_answer.is_not(None),
        )
        .order_by(PracticeMessage.round_index.asc())
        .all()
    )

    feedback = generate_practice_feedback(
        session=session,
        answered_messages=answered_messages,
    )

    session.status = "finished"
    session.feedback_json = json.dumps(feedback, ensure_ascii=False)
    session.finished_at = datetime.now()
    db.commit()
    db.refresh(session)

    return session, feedback
