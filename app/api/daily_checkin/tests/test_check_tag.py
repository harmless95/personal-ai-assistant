from app.api.daily_checkin.models.daily import RequestState
from app.api.daily_checkin.utils.check_tag import state_to_tags


def test_state_to_tags_high_stress_low_energy() -> None:
    state = RequestState(
        stress_level=4,
        energy_level=2,
        plan_done=2,
        blocker_present=1,
        learning_done=3,
    )

    tags = state_to_tags(state)

    assert tags == {"stress", "low_energy", "plan_miss", "blocker", "learning_mid"}


def test_state_to_tags_calm_day() -> None:
    state = RequestState(
        stress_level=2,
        energy_level=4,
        plan_done=5,
        blocker_present=0,
        learning_done=5,
    )

    tags = state_to_tags(state)

    assert tags == set()
