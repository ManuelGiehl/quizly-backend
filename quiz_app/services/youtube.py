"""Extract and normalize YouTube video URLs to canonical watch?v= form."""

from urllib.parse import parse_qs, urlparse

import re

_VIDEO_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def _valid_video_id(video_id: str) -> bool:
    return bool(_VIDEO_ID_PATTERN.fullmatch(video_id))


def _id_from_youtube_com(parsed) -> str | None:
    path = parsed.path or ""
    if path == "/watch" or path.startswith("/watch"):
        values = parse_qs(parsed.query).get("v")
        return values[0] if values else None
    if "/shorts/" in path:
        return path.split("/shorts/")[-1].split("/")[0].split("?")[0]
    if "/embed/" in path:
        return path.split("/embed/")[-1].split("/")[0].split("?")[0]
    return None


def _extract_video_id(raw_url: str) -> str | None:
    raw = (raw_url or "").strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").strip("/")
    if "youtube.com" in host or "youtube-nocookie.com" in host:
        return _id_from_youtube_com(parsed)
    if "youtu.be" in host:
        return path.split("/")[0].split("?")[0] if path else None
    return None


def normalize_youtube_watch_url(raw_url: str) -> str:
    """
    Return https://www.youtube.com/watch?v=<11-char id>.
    Raises ValueError if the URL is not a supported YouTube video URL.
    """
    video_id = _extract_video_id(raw_url)
    if not video_id or not _valid_video_id(video_id):
        raise ValueError("Invalid YouTube URL.")
    return f"https://www.youtube.com/watch?v={video_id}"
