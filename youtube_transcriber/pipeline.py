"""다운로드 + 음성 인식 + 파일 출력을 묶는 파이프라인."""

from __future__ import annotations

import os
import re
import tempfile
from typing import Callable, List, Optional

from . import formats
from .download import download_audio
from .transcribe import transcribe_audio


def _slugify(name: str, fallback: str) -> str:
    """파일명으로 안전한 문자열을 만든다."""
    name = name.strip()
    name = re.sub(r"[\\/:*?\"<>|]+", "_", name)  # 파일명 금지 문자 치환
    name = re.sub(r"\s+", "_", name)
    name = name.strip("._")
    return name[:120] or fallback


def transcribe_youtube(
    url: str,
    output_dir: str = "output",
    model_size: str = "base",
    language: Optional[str] = None,
    output_formats: Optional[List[str]] = None,
    device: str = "auto",
    compute_type: str = "auto",
    vad_filter: bool = True,
    keep_audio: bool = False,
    on_progress: Optional[Callable] = None,
    log: Callable[[str], None] = print,
) -> dict:
    """YouTube URL 하나를 받아 텍스트로 변환하고 파일로 저장한다.

    Returns:
        생성된 출력 파일 경로 등을 담은 dict.
    """
    output_formats = output_formats or ["srt", "vtt", "json", "txt"]
    os.makedirs(output_dir, exist_ok=True)

    # 1) 오디오 다운로드 (임시 디렉터리에 받았다가 필요 시 보관)
    audio_tmp_dir = tempfile.mkdtemp(prefix="yt_audio_")
    log(f"[1/3] 오디오 다운로드 중: {url}")
    dl = download_audio(url, audio_tmp_dir)
    log(f"      제목: {dl.title} ({dl.video_id})")

    try:
        # 2) 음성 인식
        log(f"[2/3] 음성 인식 중 (model={model_size}, language={language or 'auto'})")
        result = transcribe_audio(
            dl.audio_path,
            model_size=model_size,
            language=language,
            device=device,
            compute_type=compute_type,
            vad_filter=vad_filter,
            on_progress=on_progress,
        )
        log(
            f"      감지 언어: {result.language} "
            f"(확률 {result.language_probability:.2f}), "
            f"구간 {len(result.segments)}개"
        )

        # 3) 파일 출력
        base = _slugify(dl.title, dl.video_id)
        metadata = {
            "video_id": dl.video_id,
            "title": dl.title,
            "url": dl.webpage_url,
            "uploader": dl.uploader,
            "model": model_size,
        }

        written: List[str] = []
        log(f"[3/3] 결과 저장 중: {output_dir}")
        for fmt in output_formats:
            writer = formats.WRITERS.get(fmt)
            if writer is None:
                log(f"      경고: 알 수 없는 형식 '{fmt}' 건너뜀")
                continue
            content = (
                writer(result, metadata) if fmt == "json" else writer(result)
            )
            out_path = os.path.join(output_dir, f"{base}.{fmt}")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            written.append(out_path)
            log(f"      저장됨: {out_path}")

        # 오디오 보관 옵션
        kept_audio = None
        if keep_audio:
            ext = os.path.splitext(dl.audio_path)[1]
            kept_audio = os.path.join(output_dir, f"{base}{ext}")
            os.replace(dl.audio_path, kept_audio)
            log(f"      오디오 보관: {kept_audio}")

        return {
            "video_id": dl.video_id,
            "title": dl.title,
            "language": result.language,
            "num_segments": len(result.segments),
            "outputs": written,
            "audio": kept_audio,
        }
    finally:
        # 임시 디렉터리 정리
        try:
            if os.path.exists(dl.audio_path):
                os.remove(dl.audio_path)
            os.rmdir(audio_tmp_dir)
        except OSError:
            pass
