from app.api.daily_checkin.models.daily import QuestionCategory
from app.tasks.services.knowledge_query import build_knowledge_query


def test_build_knowledge_query_joins_sorted_answers() -> None:
    query = build_knowledge_query(
        {
            QuestionCategory.RISK: "Meetings",
            QuestionCategory.ACTION: "Ship",
            QuestionCategory.ENERGY: "  No breaks  ",
            QuestionCategory.FOCUS: "",
            QuestionCategory.LEARNING: "Scoring",
        }
    )
    assert query == "Ship No breaks Scoring Meetings"
