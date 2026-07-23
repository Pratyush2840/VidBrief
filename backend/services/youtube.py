import re
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    CouldNotRetrieveTranscript,
    NoTranscriptFound,
    TranscriptsDisabled,
)

_VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_PREFERRED_LANGUAGES = ["en", "en-US", "en-GB"]


class InvalidYouTubeURLError(Exception):
    pass


class TranscriptUnavailableError(Exception):
    pass


class TranscriptFetchError(Exception):
    pass


def extract_video_id(url: str) -> str:
    raw = url.strip()
    if not raw:
        raise InvalidYouTubeURLError("YouTube URL must not be empty.")
    if "://" not in raw:
        raw = "https://" + raw

    try:
        parsed = urlparse(raw)
    except ValueError as e:
        raise InvalidYouTubeURLError(f"Could not parse URL: {url}") from e

    hostname = (parsed.hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]

    video_id = None
    if hostname == "youtu.be":
        segments = [s for s in parsed.path.split("/") if s]
        video_id = segments[0] if segments else None
    elif hostname in ("youtube.com", "m.youtube.com", "music.youtube.com"):
        path = parsed.path
        if path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        else:
            for prefix in ("/shorts/", "/embed/", "/live/", "/v/"):
                if path.startswith(prefix):
                    video_id = path[len(prefix):].split("/")[0]
                    break

    if not video_id or not _VIDEO_ID_RE.fullmatch(video_id):
        raise InvalidYouTubeURLError(
            f"Could not extract a valid YouTube video ID from URL: {url}"
        )

    return video_id


def fetch_transcript(video_id: str) -> str:
    api = YouTubeTranscriptApi()

    try:
        transcript_list = api.list(video_id)
    except TranscriptsDisabled as e:
        raise TranscriptUnavailableError(
            "Transcripts/captions are disabled for this video."
        ) from e
    except CouldNotRetrieveTranscript as e:
        raise TranscriptFetchError(f"Could not retrieve transcript: {e}") from e
    except Exception as e:
        raise TranscriptFetchError(
            f"Unexpected error while looking up transcripts: {e}"
        ) from e

    try:
        transcript = transcript_list.find_transcript(_PREFERRED_LANGUAGES)
    except NoTranscriptFound:
        available = list(transcript_list)
        if not available:
            raise TranscriptUnavailableError(
                "No transcript is available for this video."
            )
        transcript = available[0]

    try:
        fetched = transcript.fetch()
    except Exception as e:
        raise TranscriptFetchError(f"Failed to fetch transcript content: {e}") from e

    text = " ".join(
        snippet.text.strip() for snippet in fetched if snippet.text.strip()
    )
    if not text:
        raise TranscriptUnavailableError("Transcript for this video is empty.")

    return text
