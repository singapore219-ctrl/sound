"""FastAPI 기반 웹 서버.

브라우저에서 YouTube URL 을 입력하면 백그라운드 스레드에서 다운로드 →
음성 인식 → 저장을 수행하고, SSE(Server-Sent Events) 로 진행 상황과
인식된 자막 구간을 실시간 전송한다.
"""

from __future__ import annotations

import json
import os
import queue
import tempfile
import threading
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from fastapi import FastAPI
from fastapi.responses import (
    FileResponse,
    HTMLResponse,
    JSONResponse,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from youtube_transcriber import formats
from youtube_transcriber.download import download_audio
from youtube_transcriber.pipeline import _slugify
from youtube_transcriber.transcribe import transcribe_audio

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(HERE, "static")
JOBS_DIR = os.path.join(os.getcwd(), "output", "web")

app = FastAPI(title="sound — YouTube 음성→텍스트")


# --------------------------------------------------------------------------- #
# 작업(Job) 관리
# --------------------------------------------------------------------------- #
@dataclass
class Job:
    id: str
    events: "queue.Queue[dict]" = field(default_factory=queue.Queue)
    done: bool = False
    outputs: Dict[str, str] = field(default_factory=dict)  # fmt -> 파일 경로


JOBS: Dict[str, Job] = {}
SENTINEL = {"type": "__end__"}


class TranscribeRequest(BaseModel):
    url: str
    model: str = "base"
    language: Optional[str] = None
    formats: List[str] = ["srt", "vtt", "json", "txt"]
    device: str = "auto"
    compute_type: str = "auto"
    vad: bool = True


def _run_job(job: Job, req: TranscribeRequest) -> None:
    """백그라운드 스레드에서 실제 변환을 수행한다."""

    def emit(event: dict) -> None:
        job.events.put(event)

    audio_tmp_dir = tempfile.mkdtemp(prefix="yt_audio_")
    audio_path: Optional[str] = None
    try:
        emit({"type": "status", "message": "오디오 다운로드 중…"})
        dl = download_audio(req.url, audio_tmp_dir)
        audio_path = dl.audio_path
        emit(
            {
                "type": "meta",
                "title": dl.title,
                "video_id": dl.video_id,
                "url": dl.webpage_url,
                "uploader": dl.uploader,
                "duration": dl.duration,
            }
        )

        emit(
            {
                "type": "status",
                "message": f"음성 인식 중… (모델 {req.model}, "
                f"언어 {req.language or '자동 감지'})",
            }
        )

        def on_segment(seg) -> None:
            emit(
                {
                    "type": "segment",
                    "index": seg.index,
                    "start": seg.start,
                    "end": seg.end,
                    "text": seg.text,
                }
            )

        result = transcribe_audio(
            audio_path,
            model_size=req.model,
            language=req.language,
            device=req.device,
            compute_type=req.compute_type,
            vad_filter=req.vad,
            on_progress=on_segment,
        )

        emit({"type": "status", "message": "결과 파일 저장 중…"})
        job_out_dir = os.path.join(JOBS_DIR, job.id)
        os.makedirs(job_out_dir, exist_ok=True)
        base = _slugify(dl.title, dl.video_id)
        metadata = {
            "video_id": dl.video_id,
            "title": dl.title,
            "url": dl.webpage_url,
            "uploader": dl.uploader,
            "model": req.model,
        }
        for fmt in req.formats:
            writer = formats.WRITERS.get(fmt)
            if writer is None:
                continue
            content = writer(result, metadata) if fmt == "json" else writer(result)
            out_path = os.path.join(job_out_dir, f"{base}.{fmt}")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            job.outputs[fmt] = out_path

        emit(
            {
                "type": "done",
                "language": result.language,
                "language_probability": round(result.language_probability, 3),
                "num_segments": len(result.segments),
                "text": result.text,
                "formats": list(job.outputs.keys()),
            }
        )
    except Exception as exc:  # noqa: BLE001 - 사용자에게 오류 메시지 전달
        emit({"type": "error", "message": str(exc)})
    finally:
        # 임시 오디오 정리
        try:
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)
            os.rmdir(audio_tmp_dir)
        except OSError:
            pass
        job.done = True
        job.events.put(SENTINEL)


# --------------------------------------------------------------------------- #
# API 엔드포인트
# --------------------------------------------------------------------------- #
@app.post("/api/transcribe")
def start_transcribe(req: TranscribeRequest) -> JSONResponse:
    if not req.url.strip():
        return JSONResponse({"error": "URL 을 입력하세요."}, status_code=400)
    job = Job(id=uuid.uuid4().hex[:12])
    JOBS[job.id] = job
    threading.Thread(target=_run_job, args=(job, req), daemon=True).start()
    return JSONResponse({"job_id": job.id})


@app.get("/api/stream/{job_id}")
def stream(job_id: str) -> StreamingResponse:
    job = JOBS.get(job_id)
    if job is None:
        return JSONResponse({"error": "작업을 찾을 수 없습니다."}, status_code=404)

    def event_gen():
        while True:
            event = job.events.get()
            if event is SENTINEL:
                break
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/download/{job_id}/{fmt}")
def download(job_id: str, fmt: str):
    job = JOBS.get(job_id)
    if job is None or fmt not in job.outputs:
        return JSONResponse({"error": "파일을 찾을 수 없습니다."}, status_code=404)
    path = job.outputs[fmt]
    return FileResponse(
        path,
        filename=os.path.basename(path),
        media_type="application/octet-stream",
    )


@app.get("/", response_class=HTMLResponse)
def index() -> HTMLResponse:
    with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


# 정적 파일 (CSS/JS)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
