from app.api.daily_checkin.models.daily import RequestState


def state_to_tags(state: RequestState) -> set[str]:
    tags = set()
    if state.stress_level >= 4:
        tags.add("stress")
    if state.energy_level <= 2:
        tags.add("low_energy")
    if state.plan_done <= 2:
        tags.add("plan_miss")
    if state.blocker_present == 1:
        tags.add("blocker")
    if state.learning_done == 3:
        tags.add("learning_mid")
    return tags
