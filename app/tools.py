from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Module:
    name: str
    objective: str
    exercise: str


def detect_modules(goal: str) -> list[Module]:
    """A deterministic intent tool: map goal keywords to learning modules."""
    text = goal.lower()
    modules: list[Module] = []
    if any(word in text for word in ("python", "backend", "api", "fastapi")):
        modules.extend(
            [
                Module("Nền tảng Python", "Nắm cú pháp, kiểu dữ liệu và hàm", "Viết 3 bài tập xử lý dữ liệu nhỏ"),
                Module("Xây dựng API", "Thiết kế endpoint và validation", "Tạo một API CRUD nhỏ"),
                Module("Kiểm thử và triển khai", "Viết test và đóng gói ứng dụng", "Viết test cho 2 endpoint"),
            ]
        )
    elif any(word in text for word in ("english", "tiếng anh", "ielts", "toeic")):
        modules.extend(
            [
                Module("Từ vựng theo chủ đề", "Mở rộng vốn từ có ngữ cảnh", "Ôn 20 từ bằng flashcard"),
                Module("Nghe và phát âm", "Cải thiện khả năng nhận diện âm thanh", "Nghe 10 phút và chép chính tả"),
                Module("Viết và phản hồi", "Diễn đạt ý rõ ràng", "Viết một đoạn 120 từ"),
            ]
        )
    else:
        modules.extend(
            [
                Module("Khái niệm cốt lõi", "Xây nền tảng cho mục tiêu", "Tóm tắt 5 ý chính bằng ghi chú"),
                Module("Thực hành có hướng dẫn", "Chuyển kiến thức thành kỹ năng", "Hoàn thành một bài thực hành nhỏ"),
                Module("Ôn tập và dự án", "Củng cố và tạo sản phẩm", "Tạo một sản phẩm đầu ra đơn giản"),
            ]
        )
    return modules


def distribute_hours(total_hours: float, slots: int) -> list[float]:
    """Split hours across slots while keeping useful precision."""
    if slots <= 0:
        return []
    base = round(total_hours / slots, 2)
    values = [base] * slots
    values[-1] = round(total_hours - sum(values[:-1]), 2)
    return values

