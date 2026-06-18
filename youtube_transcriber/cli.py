"""명령줄 인터페이스."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .pipeline import transcribe_youtube

MODEL_CHOICES = [
    "tiny",
    "base",
    "small",
    "medium",
    "large-v2",
    "large-v3",
]
FORMAT_CHOICES = ["srt", "vtt", "txt", "json"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="youtube-transcriber",
        description="YouTube 영상의 음성을 텍스트(자막/JSON)로 변환합니다.",
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="변환할 YouTube 영상 URL (여러 개 지정 가능)",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        default="output",
        help="결과 저장 디렉터리 (기본값: output)",
    )
    parser.add_argument(
        "-m",
        "--model",
        default="base",
        choices=MODEL_CHOICES,
        help="Whisper 모델 크기 (기본값: base). 클수록 정확하지만 느림",
    )
    parser.add_argument(
        "-l",
        "--language",
        default=None,
        help="언어 코드(예: ko, en). 지정하지 않으면 자동 감지",
    )
    parser.add_argument(
        "-f",
        "--formats",
        nargs="+",
        default=["srt", "vtt", "json", "txt"],
        choices=FORMAT_CHOICES,
        help="출력 형식 (기본값: srt vtt json txt)",
    )
    parser.add_argument(
        "--device",
        default="auto",
        choices=["auto", "cpu", "cuda"],
        help="연산 장치 (기본값: auto)",
    )
    parser.add_argument(
        "--compute-type",
        default="auto",
        help="연산 정밀도(int8, float16 등) 또는 auto (기본값: auto)",
    )
    parser.add_argument(
        "--no-vad",
        action="store_true",
        help="무음 제거(VAD) 필터를 끕니다",
    )
    parser.add_argument(
        "--keep-audio",
        action="store_true",
        help="다운로드한 오디오 파일을 결과 디렉터리에 보관합니다",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="구간별 실시간 출력을 끕니다",
    )
    return parser


def _make_progress_callback(enabled: bool):
    if not enabled:
        return None

    def _cb(seg):
        sys.stderr.write(f"  [{seg.start:7.1f}s] {seg.text}\n")
        sys.stderr.flush()

    return _cb


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    on_progress = _make_progress_callback(not args.no_progress)

    exit_code = 0
    for url in args.urls:
        try:
            transcribe_youtube(
                url,
                output_dir=args.output_dir,
                model_size=args.model,
                language=args.language,
                output_formats=args.formats,
                device=args.device,
                compute_type=args.compute_type,
                vad_filter=not args.no_vad,
                keep_audio=args.keep_audio,
                on_progress=on_progress,
            )
        except Exception as exc:  # noqa: BLE001 - CLI 최상단에서 한 영상 실패가 전체를 막지 않도록
            sys.stderr.write(f"[오류] {url} 처리 실패: {exc}\n")
            exit_code = 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
