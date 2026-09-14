from typing import Literal

from pydantic import BaseModel, Field, field_validator


class SlideContent(BaseModel):
    heading: str | None = None
    bullet_points: list[str] = Field(default_factory=list)
    left_item: str | None = None
    right_item: str | None = None
    code_snippet: str | None = None
    visual_hint: str | None = None


class Slide(BaseModel):
    slide_id: str
    type: Literal["title", "concept", "comparison", "diagram", "code", "summary"]
    narration: str
    content: SlideContent = Field(default_factory=SlideContent)
    estimated_duration_seconds: int = Field(default=10, ge=1, le=120)


class TeachingScript(BaseModel):
    lesson_id: str
    language: Literal["ar", "en"] = "ar"
    target_duration_seconds: int = Field(default=180, ge=1, le=600)
    slides: list[Slide] = Field(min_length=2)

    @field_validator("slides")
    @classmethod
    def validate_boundaries(cls, slides: list[Slide]) -> list[Slide]:
        if slides[0].type != "title":
            raise ValueError("The first slide must be title")
        if slides[-1].type != "summary":
            raise ValueError("The last slide must be summary")
        return slides


def normalize_legacy_script(script: dict, lesson_id: str) -> TeachingScript:
    slides = [
        Slide(
            slide_id="title",
            type="title",
            narration=script["introduction"],
            content=SlideContent(heading=script["title"]),
            estimated_duration_seconds=10,
        )
    ]
    for index, section in enumerate(script["sections"], start=1):
        narration = str(section.get("explanation", "")).strip()
        if narration:
            slides.append(
                Slide(
                    slide_id=f"section-{index}",
                    type="concept",
                    narration=narration,
                    content=SlideContent(heading=section.get("heading")),
                    estimated_duration_seconds=max(5, round(len(narration.split()) / 2.3)),
                )
            )
    slides.append(
        Slide(
            slide_id="summary",
            type="summary",
            narration=script["summary"],
            content=SlideContent(heading="Summary"),
            estimated_duration_seconds=10,
        )
    )
    return TeachingScript(
        lesson_id=lesson_id,
        target_duration_seconds=max(180, min(600, sum(slide.estimated_duration_seconds for slide in slides))),
        slides=slides,
    )
