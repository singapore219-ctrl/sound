"""yt-dlp 를 이용해 YouTube 영상에서 오디오를 내려받는 모듈."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class DownloadResult:
    """다운로드 결과."""

    audio_path: str
    video_id: str
    title: str
    duration: Optional[float]
    webpage_url: str
    uploader: Optional[str]


def download_audio(url: str, output_dir: str, quiet: bool = True) -> DownloadResult:
    """주어진 YouTube URL 에서 가장 좋은 오디오 트랙을 내려받는다.

    오디오는 재인코딩 없이 원본 컨테이너 그대로 저장한다. faster-whisper 가
    PyAV(번들된 ffmpeg)로 직접 디코딩하므로 별도 ffmpeg 후처리가 필요 없다.

    Args:
        url: YouTube 영상 URL.
        output_dir: 오디오를 저장할 디렉터리.
        quiet: yt-dlp 로그 출력을 억제할지 여부.

    Returns:
        다운로드된 오디오 경로와 메타데이터를 담은 ``DownloadResult``.
    """
    import yt_dlp  # 무거운 의존성이므로 함수 안에서 import 한다.

    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": os.path.join(output_dir, "%(id)s.%(ext)s"),
        "quiet": quiet,
        "no_warnings": quiet,
        "noprogress": quiet,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        audio_path = ydl.prepare_filename(info)

    return DownloadResult(
        audio_path=audio_path,
        video_id=info.get("id", ""),
        title=info.get("title", ""),
        duration=info.get("duration"),
        webpage_url=info.get("webpage_url", url),
        uploader=info.get("uploader"),
    )
