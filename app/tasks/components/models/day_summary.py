from dataclasses import dataclass

from app.api.daily_checkin.models.daily import AnswerCheckinResponse, ArtifactSource


@dataclass(frozen=True, slots=True)
class DaySummaryBuildResult:
    response: AnswerCheckinResponse
    source: ArtifactSource
