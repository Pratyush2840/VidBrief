import asyncio
import json
import re

from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from config import settings
from models.schemas import SummarizeResult

# Gemini 2.5 Flash has a huge context window, so most YouTube transcripts fit
# in a single call. This threshold is a safety net for unusually long videos
# (multi-hour lectures/streams) -- above it we map-reduce instead of relying
# on one giant prompt.
MAP_REDUCE_THRESHOLD_CHARS = 60_000
CHUNK_SIZE_CHARS = 45_000
MAX_ATTEMPTS = 2

_client = genai.Client(api_key=settings.gemini_api_key)

_PIPELINE_INSTRUCTION = """You are an expert study-guide creator. Given a YouTube video transcript (or a condensed synthesis of one), produce a JSON object with EXACTLY these keys:

- "summary": a concise, well-written prose summary of the video (3-6 sentences).
- "notes": an array of sections, each an object with "heading" (short string) and "points" (array of concise bullet-point strings covering key facts/ideas). Include as many sections as needed to cover the material, typically 3-8.
- "quiz": an array of 5 to 8 multiple-choice questions, each an object with "question" (string), "options" (array of exactly 4 plausible answer strings), and "correct_index" (0-based integer index into "options" for the correct answer).
- "flashcards": an array of at least 5 Q&A flashcards, each an object with "front" (a question or term) and "back" (the answer/definition).

Rules:
- Base everything strictly on the transcript content. Do not invent facts it doesn't support.
- Return ONLY raw JSON matching that shape. No markdown code fences, no commentary, no trailing text before or after the JSON.
- Ensure the JSON is strictly valid: correctly escaped strings, no trailing commas, no comments.
"""

_RETRY_SUFFIX = "\n\nIMPORTANT: Your previous response was not valid JSON matching the required schema. Respond with ONLY a single valid JSON object, no markdown fences, no extra text."

_CHUNK_SUMMARY_INSTRUCTION = """You are condensing part {index} of {total} of a long video transcript. Write a dense, factual summary of this part that preserves concrete facts, names, numbers, arguments, and key points, so it can later be combined with summaries of the other parts to build study materials. Omit filler and small talk. Plain prose or bullet points only -- no JSON, no headers, no mention of "part {index}"."""


class GeminiOutputError(Exception):
    pass


def _chunk_text(text: str, chunk_size: int) -> list[str]:
    words = text.split(" ")
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0
    for word in words:
        current.append(word)
        current_len += len(word) + 1
        if current_len >= chunk_size:
            chunks.append(" ".join(current))
            current = []
            current_len = 0
    if current:
        chunks.append(" ".join(current))
    return chunks


def _extract_json(raw_text: str) -> dict:
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


async def _generate_text(
    prompt: str, system_instruction: str, *, json_mode: bool, temperature: float
) -> str:
    try:
        response = await _client.aio.models.generate_content(
            model=settings.gemini_model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json" if json_mode else None,
                temperature=temperature,
            ),
        )
    except genai_errors.APIError as e:
        raise GeminiOutputError(f"Gemini API request failed: {e}") from e

    if not response.text:
        raise GeminiOutputError("Gemini returned an empty response.")
    return response.text


async def _summarize_chunk(chunk: str, index: int, total: int) -> str:
    instruction = _CHUNK_SUMMARY_INSTRUCTION.format(index=index + 1, total=total)
    text = await _generate_text(chunk, instruction, json_mode=False, temperature=0.2)
    return text.strip()


async def _condense_via_map_reduce(transcript: str) -> str:
    chunks = _chunk_text(transcript, CHUNK_SIZE_CHARS)
    summaries = await asyncio.gather(
        *(_summarize_chunk(chunk, i, len(chunks)) for i, chunk in enumerate(chunks))
    )
    return "\n\n".join(summaries)


async def _run_pipeline_prompt(transcript: str) -> SummarizeResult:
    last_error: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        prompt = f"Transcript:\n\n{transcript}"
        if attempt > 0:
            prompt += _RETRY_SUFFIX
        try:
            raw_text = await _generate_text(
                prompt, _PIPELINE_INSTRUCTION, json_mode=True, temperature=0.4
            )
            data = _extract_json(raw_text)
            return SummarizeResult.model_validate(data)
        except (json.JSONDecodeError, ValidationError, GeminiOutputError) as e:
            last_error = e
            continue

    raise GeminiOutputError(
        f"Gemini did not return valid structured output after {MAX_ATTEMPTS} attempts: {last_error}"
    )


async def generate_study_pack(transcript: str) -> SummarizeResult:
    text_for_pipeline = transcript
    if len(transcript) > MAP_REDUCE_THRESHOLD_CHARS:
        text_for_pipeline = await _condense_via_map_reduce(transcript)

    return await _run_pipeline_prompt(text_for_pipeline)
