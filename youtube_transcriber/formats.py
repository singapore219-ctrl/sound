"""음성 인식 결과를 SRT/VTT/JSON/TXT 형식으로 직렬화하는 모듈."""

from __future__ import annotations

import json
from typing import Dict

from .transcribe import TranscriptionResult


def _format_timestamp(seconds: float, separator: str = ",") -> str:
    """초 단위 시간을 ``HH:MM:SS,mmm`` 형태 문자열로 변환한다.

    SRT 는 밀리초 구분자로 콤마(``,``)를, VTT 는 점(``.``)을 사용한다.
    """
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}{separator}{millis:03d}"


def to_srt(result: TranscriptionResult) -> str:
    """결과를 SRT 자막 문자열로 변환한다."""
    blocks = []
    for seg in result.segments:
        start = _format_timestamp(seg.start, ",")
        end = _format_timestamp(seg.end, ",")
        blocks.append(f"{seg.index}\n{start} --> {end}\n{seg.text}")
    return "\n\n".join(blocks) + ("\n" if blocks else "")


def to_vtt(result: TranscriptionResult) -> str:
    """결과를 WebVTT 자막 문자열로 변환한다."""
    blocks = ["WEBVTT", ""]
    for seg in result.segments:
        start = _format_timestamp(seg.start, ".")
        end = _format_timestamp(seg.end, ".")
        blocks.append(f"{start} --> {end}\n{seg.text}")
    return "\n\n".join(blocks) + "\n"


def to_txt(result: TranscriptionResult) -> str:
    """결과를 한 줄에 한 구간씩 담은 평문으로 변환한다."""
    return "\n".join(seg.text for seg in result.segments) + (
        "\n" if result.segments else ""
    )


def to_json(result: TranscriptionResult, metadata: Dict | None = None) -> str:
    """결과를 세그먼트와 메타데이터를 담은 JSON 문자열로 변환한다."""
    payload = {
        "metadata": metadata or {},
        "language": result.language,
        "language_probability": round(result.language_probability, 4),
        "duration": round(result.duration, 3),
        "text": result.text,
        "segments": [
            {
                "index": seg.index,
                "start": round(seg.start, 3),
                "end": round(seg.end, 3),
                "text": seg.text,
            }
            for seg in result.segments
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# 확장자 -> 직렬화 함수 매핑
WRITERS = {
    "srt": to_srt,
    "vtt": to_vtt,
    "txt": to_txt,
    "json": to_json,
}
