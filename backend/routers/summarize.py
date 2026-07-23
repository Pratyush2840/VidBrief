import logging

from fastapi import APIRouter, HTTPException, Request

from config import settings
from limiter import limiter
from models.schemas import SummarizeRequest, SummarizeResponse
from services import youtube
from services.cache import result_cache
from services.gemini import GeminiOutputError, generate_study_pack
from services.youtube import (
    InvalidYouTubeURLError,
    TranscriptFetchError,
    TranscriptUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/summarize", response_model=SummarizeResponse)
@limiter.limit(settings.rate_limit)
async def summarize(request: Request, body: SummarizeRequest) -> SummarizeResponse:
    try:
        video_id = youtube.extract_video_id(body.youtube_url)
    except InvalidYouTubeURLError as e:
        raise HTTPException(status_code=400, detail=str(e))

    cached = result_cache.get(video_id)
    if cached is not None:
        return SummarizeResponse(**cached, video_id=video_id, cached=True)

    try:
        transcript = youtube.fetch_transcript(video_id)
    except TranscriptUnavailableError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except TranscriptFetchError as e:
        raise HTTPException(status_code=502, detail=str(e))

    try:
        result = await generate_study_pack(transcript)
    except GeminiOutputError as e:
        logger.exception("Gemini pipeline failed for video %s", video_id)
        raise HTTPException(status_code=502, detail=f"AI generation failed: {e}")

    result_cache.set(video_id, result.model_dump())

    return SummarizeResponse(**result.model_dump(), video_id=video_id, cached=False)
