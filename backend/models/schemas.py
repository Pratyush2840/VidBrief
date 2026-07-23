from pydantic import BaseModel, Field, field_validator


class SummarizeRequest(BaseModel):
    youtube_url: str


class NoteSection(BaseModel):
    heading: str
    points: list[str]


class QuizQuestion(BaseModel):
    question: str
    options: list[str]
    correct_index: int

    @field_validator("options")
    @classmethod
    def options_len(cls, v: list[str]) -> list[str]:
        if len(v) < 2:
            raise ValueError("options must contain at least 2 items")
        return v

    @field_validator("correct_index")
    @classmethod
    def index_in_range(cls, v: int, info) -> int:
        options = info.data.get("options")
        if options is not None and not (0 <= v < len(options)):
            raise ValueError("correct_index out of range for options")
        return v


class Flashcard(BaseModel):
    front: str
    back: str


class SummarizeResult(BaseModel):
    summary: str
    notes: list[NoteSection]
    quiz: list[QuizQuestion] = Field(min_length=1)
    flashcards: list[Flashcard] = Field(min_length=1)


class SummarizeResponse(SummarizeResult):
    video_id: str
    cached: bool = False


class ErrorResponse(BaseModel):
    detail: str
