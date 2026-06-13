from sqlalchemy.orm import Session

from app.models import Question


DEFAULT_QUESTIONS = [
    {
        "part": "Part 1",
        "topic": "Work or Study",
        "content": "Do you work or are you a student?",
    },
    {
        "part": "Part 1",
        "topic": "Hometown",
        "content": "Where is your hometown?",
    },
    {
        "part": "Part 1",
        "topic": "Daily Routine",
        "content": "What do you usually do on weekends?",
    },
    {
        "part": "Part 2",
        "topic": "Person",
        "content": "Describe a person who inspired you.",
    },
    {
        "part": "Part 2",
        "topic": "Place",
        "content": "Describe a place you like to visit.",
    },
    {
        "part": "Part 3",
        "topic": "Technology",
        "content": "How has technology changed the way people communicate?",
    },
]


def init_default_questions(db: Session) -> None:
    """
    初始化默认题库。

    如果数据库里已经有题目，就不重复插入。
    """
    existing_count = db.query(Question).count()
    if existing_count > 0:
        return

    questions = [Question(**item) for item in DEFAULT_QUESTIONS]
    db.add_all(questions)
    db.commit()


def list_questions(db: Session) -> list[Question]:
    """
    查询所有题目。
    """
    return db.query(Question).order_by(Question.id.asc()).all()
