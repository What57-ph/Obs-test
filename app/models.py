from __future__ import annotations

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class StudyPlanRequest(BaseModel):
    goal: str = Field(..., min_length=5, max_length=500, description="Mục tiêu học tập")
    weekly_hours: float = Field(..., gt=0, le=40)
    weeks: int = Field(default=4, ge=1, le=52)
    current_level: Literal["beginner", "intermediate", "advanced"] = "beginner"
    preferred_days: list[str] = Field(default_factory=lambda: ["Mon", "Wed", "Fri"])

    @field_validator("goal")
    @classmethod
    def normalize_goal(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not normalized:
            raise ValueError("goal không được rỗng")
        return normalized

    @field_validator("preferred_days")
    @classmethod
    def validate_days(cls, value: list[str]) -> list[str]:
        allowed = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
        clean = list(dict.fromkeys(day.strip().title() for day in value if day.strip()))
        if not clean or any(day not in allowed for day in clean):
            raise ValueError("preferred_days phải chứa ngày dạng Mon/Tue/Wed/Thu/Fri/Sat/Sun")
        return clean


class StudyBlock(BaseModel):
    week: int
    day: str
    topic: str
    duration_hours: float = Field(gt=0)
    exercise: str


class StudyPlanResponse(BaseModel):
    plan_id: UUID
    title: str
    summary: str
    assumptions: list[str]
    weekly_schedule: list[StudyBlock]
    next_actions: list[str]
    metadata: dict[str, str | int | float]


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    environment: str
    agent_mode: str


class ErrorResponse(BaseModel):
    error: dict[str, str]

