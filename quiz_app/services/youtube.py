"""YouTube: canonical URL parsing and yt-dlp (metadata + best-audio download)."""

from pathlib import Path
from urllib.parse import parse_qs, urlparse

import re
import yt_dlp
from yt_dlp.utils import DownloadError

_VIDEO_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{11}$")


def _valid_video_id(video_id: str) -> bool:
    """Return True if the string matches the 11-char YouTube video id format."""
    return bool(_VIDEO_ID_PATTERN.fullmatch(video_id))


def _id_from_youtube_com(parsed) -> str | None:
    """Extract a video id from common youtube.com URL shapes (watch/shorts/embed)."""
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
    """Parse supported YouTube URLs and return the raw video id, otherwise None."""
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


def extract_youtube_metadata(raw_url: str) -> dict:
    """
    Fetch JSON-serializable metadata (no files written).

    Uses ``extract_info(..., download=False)`` and ``sanitize_info``.
    """
    url = normalize_youtube_watch_url(raw_url)
    opts = {"quiet": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return ydl.sanitize_info(info)
    except DownloadError as exc:
        raise ValueError("Could not fetch video metadata.") from exc


def build_audio_download_options(output_template: str) -> dict:
    """Return ``ydl_opts`` for best-audio download (per project checklist)."""
    return {
        "format": "bestaudio/best",
        "outtmpl": output_template,
        "quiet": True,
        "noplaylist": True,
    }


def _resolved_download_path(url: str, opts: dict) -> str:
    """Download via yt-dlp and return the resolved file path on disk."""
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        path = info.get("filepath") or ydl.prepare_filename(info)
    return str(Path(path).resolve())


def download_best_audio(canonical_or_raw_url: str, output_template: str) -> str:
    """
    Download the best audio stream to disk.

    ``output_template`` is ``outtmpl`` for yt-dlp (e.g. path with ``%(ext)s``).
    Returns the resolved path of the downloaded file.
    """
    url = normalize_youtube_watch_url(canonical_or_raw_url)
    opts = build_audio_download_options(output_template)
    try:
        return _resolved_download_path(url, opts)
    except DownloadError as exc:
        raise ValueError("Could not download audio from this URL.") from exc
