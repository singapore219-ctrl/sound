"""faster-whisper 를 이용한 음성 인식(STT) 모듈."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Segment:
    """음성 인식 결과의 한 구간."""

    index: int
    start: float
    end: float
    text: str


@dataclass
class TranscriptionResult:
    """전체 음성 인식 결과."""

    segments: List[Segment]
    language: str
    language_probability: float
    duration: float

    @property
    def text(self) -> str:
        """전체 구간을 줄바꿈 없이 이어 붙인 평문 텍스트."""
        return " ".join(seg.text for seg in self.segments).strip()


def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    language: Optional[str] = None,
    device: str = "auto",
    compute_type: str = "auto",
    beam_size: int = 5,
    vad_filter: bool = True,
    on_progress=None,
) -> TranscriptionResult:
    """오디오 파일을 텍스트로 변환한다.

    Args:
        audio_path: 입력 오디오 파일 경로.
        model_size: Whisper 모델 크기(tiny/base/small/medium/large-v3 등).
        language: 언어 코드(예: ``ko``, ``en``). ``None`` 이면 자동 감지.
        device: ``cpu``, ``cuda`` 또는 ``auto``.
        compute_type: 연산 정밀도(``int8``, ``float16`` 등) 또는 ``auto``.
        beam_size: 빔 서치 크기.
        vad_filter: 무음 구간 제거(VAD) 적용 여부.
        on_progress: ``Segment`` 하나를 인자로 받는 선택적 콜백.

    Returns:
        구간 리스트와 감지 언어 등을 담은 ``TranscriptionResult``.
    """
    # 무거운 의존성이므로 함수 안에서 import 한다.
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    raw_segments, info = model.transcribe(
        audio_path,
        language=language,
        beam_size=beam_size,
        vad_filter=vad_filter,
    )

    segments: List[Segment] = []
    for i, seg in enumerate(raw_segments):
        item = Segment(
            index=i + 1,
            start=seg.start,
            end=seg.end,
            text=seg.text.strip(),
        )
        segments.append(item)
        if on_progress is not None:
            on_progress(item)

    return TranscriptionResult(
        segments=segments,
        language=info.language,
        language_probability=info.language_probability,
        duration=info.duration,
    )
