"""형식 변환 로직(외부 의존성 없는 순수 함수) 테스트."""

import json

from youtube_transcriber.formats import (
    _format_timestamp,
    to_json,
    to_srt,
    to_txt,
    to_vtt,
)
from youtube_transcriber.transcribe import Segment, TranscriptionResult


def _sample_result() -> TranscriptionResult:
    return TranscriptionResult(
        segments=[
            Segment(index=1, start=0.0, end=2.5, text="안녕하세요"),
            Segment(index=2, start=2.5, end=3661.789, text="반갑습니다"),
        ],
        language="ko",
        language_probability=0.99,
        duration=3661.789,
    )


def test_format_timestamp_srt_and_vtt():
    assert _format_timestamp(0.0, ",") == "00:00:00,000"
    assert _format_timestamp(3661.789, ",") == "01:01:01,789"
    assert _format_timestamp(3661.789, ".") == "01:01:01.789"
    # 음수는 0으로 보정
    assert _format_timestamp(-5, ",") == "00:00:00,000"


def test_to_srt_structure():
    srt = to_srt(_sample_result())
    assert srt.startswith("1\n00:00:00,000 --> 00:00:02,500\n안녕하세요")
    assert "2\n00:00:02,500 --> 01:01:01,789\n반갑습니다" in srt


def test_to_vtt_has_header():
    vtt = to_vtt(_sample_result())
    assert vtt.startswith("WEBVTT\n")
    assert "00:00:00.000 --> 00:00:02.500" in vtt


def test_to_txt_one_line_per_segment():
    txt = to_txt(_sample_result())
    assert txt == "안녕하세요\n반갑습니다\n"


def test_to_json_roundtrip():
    payload = json.loads(to_json(_sample_result(), {"video_id": "abc"}))
    assert payload["language"] == "ko"
    assert payload["metadata"]["video_id"] == "abc"
    assert len(payload["segments"]) == 2
    assert payload["text"] == "안녕하세요 반갑습니다"
    assert payload["segments"][0]["start"] == 0.0


def test_empty_result_does_not_crash():
    empty = TranscriptionResult(segments=[], language="en", language_probability=0.5, duration=0.0)
    assert to_srt(empty) == ""
    assert to_txt(empty) == ""
    assert to_vtt(empty).startswith("WEBVTT")
