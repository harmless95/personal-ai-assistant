from typing import Any


def format_artifact(artifact: dict[str, Any]) -> str:
    status = artifact.get("status", "unknown")
    if status == "pending":
        return "⏳ Итог дня ещё готовится…"
    if status == "failed":
        return "❌ Не удалось сгенерировать итог дня."

    source = artifact.get("source") or "—"
    summary = artifact.get("day_summary") or "—"
    insights = artifact.get("insights") or {}
    actions = artifact.get("recommended_actions") or {}
    checkpoints = actions.get("two_checkpoints") or []
    checkpoints_text = "\n".join(f"• {item}" for item in checkpoints) or "—"

    return (
        f"✅ Итог дня (source: {source})\n\n"
        f"{summary}\n\n"
        f"🔍 Insights\n"
        f"• Risk/blocker: {insights.get('top_risk_or_blocker', '—')}\n"
        f"• Strength: {insights.get('top_strength', '—')}\n"
        f"• Learning gap: {insights.get('learning_gap', '—')}\n\n"
        f"🎯 Actions\n"
        f"• Today: {actions.get('today_action', '—')}\n"
        f"{checkpoints_text}"
    )


def format_history(items: list[dict[str, Any]]) -> str:
    if not items:
        return "История пуста. Начни с /checkin."
    lines = ["📅 История check-in:"]
    for item in items:
        lines.append(
            f"• {item.get('date', '—')} — {item.get('status', '—')} (`{item.get('checkin_id', '')}`)"
        )
    return "\n".join(lines)


def format_question(index: int, total: int, question: dict[str, Any]) -> str:
    category = question.get("category", "")
    text = question.get("text", "")
    return f"Вопрос {index}/{total} [{category}]\n\n{text}"
