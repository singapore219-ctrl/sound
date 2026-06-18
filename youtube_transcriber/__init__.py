"""YouTube 영상의 음성을 텍스트로 변환하는 패키지.

무거운 선택적 의존성(yt-dlp, faster-whisper)을 강제로 끌어오지 않도록
공개 API 는 지연(lazy) import 로 노출한다.
"""

from __future__ import annotations

__version__ = "0.1.0"

__all__ = ["download_audio", "transcribe_audio", "transcribe_youtube"]


def __getattr__(name: str):  # PEP 562 모듈 수준 지연 import
    if name == "download_audio":
        from .download import download_audio

        return download_audio
    if name == "transcribe_audio":
        from .transcribe import transcribe_audio

        return transcribe_audio
    if name == "transcribe_youtube":
        from .pipeline import transcribe_youtube

        return transcribe_youtube
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
