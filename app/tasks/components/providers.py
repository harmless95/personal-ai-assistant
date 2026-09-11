from enum import StrEnum


class DaySummaryProvider(StrEnum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    TEMPLATE = "template"
