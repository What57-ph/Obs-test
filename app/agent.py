from __future__ import annotations

import logging
from uuid import uuid4

from .models import StudyPlanRequest, StudyPlanResponse, StudyBlock
from .tools import detect_modules, distribute_hours

logger = logging.getLogger("app.agent")


class StudyPlannerAgent:
    """Small tool-using agent that turns a goal into an actionable study plan."""

    name = "study-planner-agent"
    version = "1.0.0"

    def create_plan(self, request: StudyPlanRequest) -> StudyPlanResponse:
        logger.info(
            "agent.started",
            extra={
                "event": "agent.started",
                "goal_length": len(request.goal),
                "weeks": request.weeks,
                "weekly_hours": request.weekly_hours,
            },
        )
        modules = detect_modules(request.goal)
        days = request.preferred_days
        hours = distribute_hours(request.weekly_hours, len(days))
        schedule: list[StudyBlock] = []

        for week in range(1, request.weeks + 1):
            for index, (day, duration) in enumerate(zip(days, hours)):
                module = modules[(week - 1 + index) % len(modules)]
                schedule.append(
                    StudyBlock(
                        week=week,
                        day=day,
                        topic=module.name,
                        duration_hours=duration,
                        exercise=module.exercise,
                    )
                )

        result = StudyPlanResponse(
            plan_id=uuid4(),
            title=f"Kế hoạch {request.weeks} tuần: {request.goal}",
            summary=(
                f"Lộ trình từ mức {request.current_level}, {request.weekly_hours:g} giờ/tuần "
                f"trong {request.weeks} tuần, tập trung vào {len(modules)} nhóm kỹ năng."
            ),
            assumptions=[
                "Bạn có thể học đúng số giờ đã khai báo mỗi tuần.",
                "Mỗi buổi học gồm phần học mới và một bài thực hành ngắn.",
            ],
            weekly_schedule=schedule,
            next_actions=[
                "Chọn ngày bắt đầu và đặt lịch cố định.",
                "Sau tuần đầu tiên, đánh giá tiến độ và điều chỉnh thời lượng.",
            ],
            metadata={
                "agent": self.name,
                "agent_version": self.version,
                "modules": len(modules),
                "sessions": len(schedule),
            },
        )
        logger.info(
            "agent.completed",
            extra={"event": "agent.completed", "sessions": len(schedule), "modules": len(modules)},
        )
        return result

