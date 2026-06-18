# sound — YouTube 음성 → 텍스트 변환기

YouTube 영상에서 사람이 말하는 모든 내용을 텍스트로 변환합니다.
오디오를 내려받아 [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
(로컬 Whisper) 로 음성 인식한 뒤, 자막/JSON/평문으로 저장합니다.

- **로컬 처리**: API 키·비용 없이 오프라인으로 동작 (GPU 있으면 더 빠름)
- **자동 언어 감지**: 다국어 영상 지원 (`--language` 로 강제 지정 가능)
- **다양한 출력 형식**: `srt`, `vtt`, `json`, `txt`

## 동작 흐름

```
YouTube URL → (yt-dlp) 오디오 다운로드 → (faster-whisper) STT → SRT / VTT / JSON / TXT
```

## 설치

```bash
pip install -r requirements.txt
# 또는 패키지로 설치 (youtube-transcriber 명령 등록)
pip install -e .
```

> 참고: 큰 모델(`large-v3` 등)은 처음 실행 시 모델 가중치를 자동으로 내려받습니다.

## 사용법

```bash
# 기본 (base 모델, 자동 언어 감지, srt/vtt/json/txt 모두 출력)
python -m youtube_transcriber "https://www.youtube.com/watch?v=VIDEO_ID"

# 패키지 설치 후에는
youtube-transcriber "https://www.youtube.com/watch?v=VIDEO_ID"
```

### 자주 쓰는 옵션

| 옵션 | 설명 | 기본값 |
| --- | --- | --- |
| `-o, --output-dir` | 결과 저장 디렉터리 | `output` |
| `-m, --model` | 모델 크기 (`tiny`/`base`/`small`/`medium`/`large-v2`/`large-v3`) | `base` |
| `-l, --language` | 언어 코드(`ko`, `en` 등). 미지정 시 자동 감지 | 자동 |
| `-f, --formats` | 출력 형식 (`srt vtt json txt` 중 택) | 전부 |
| `--device` | `auto`/`cpu`/`cuda` | `auto` |
| `--compute-type` | `int8`, `float16` 등 또는 `auto` | `auto` |
| `--no-vad` | 무음 제거(VAD) 필터 끄기 | 켜짐 |
| `--keep-audio` | 내려받은 오디오 보관 | 꺼짐 |

### 예시

```bash
# 한국어로 강제, 더 정확한 모델, JSON+SRT만 출력
python -m youtube_transcriber -l ko -m large-v3 -f srt json \
  "https://youtu.be/VIDEO_ID"

# 여러 영상 한 번에
python -m youtube_transcriber URL1 URL2 URL3
```

## 출력 예시

`output/<영상제목>.srt`, `.vtt`, `.txt`, `.json` 가 생성됩니다. JSON 은 다음과 같은
구조를 가집니다.

```json
{
  "metadata": { "video_id": "...", "title": "...", "url": "...", "model": "base" },
  "language": "ko",
  "language_probability": 0.99,
  "duration": 123.45,
  "text": "전체 평문 ...",
  "segments": [
    { "index": 1, "start": 0.0, "end": 2.5, "text": "안녕하세요" }
  ]
}
```

## 웹 UI

브라우저에서 URL 을 붙여넣고 버튼만 누르면 됩니다. 인식되는 자막이
**실시간으로** 화면에 나타나고, 끝나면 SRT/VTT/JSON/TXT 를 내려받을 수 있습니다.

```bash
pip install -r requirements-web.txt
python -m webapp            # http://127.0.0.1:8000

# 외부 접속을 허용하려면
HOST=0.0.0.0 PORT=8000 python -m webapp
```

- 실시간 진행 상황은 SSE(Server-Sent Events) 로 전송됩니다.
- 모델/언어/장치/출력 형식을 화면의 "고급 옵션"에서 바로 고를 수 있습니다.

## 프로젝트 구조

```
youtube_transcriber/    # 핵심 라이브러리 + CLI
├── download.py    # yt-dlp 오디오 다운로드
├── transcribe.py  # faster-whisper STT 래퍼
├── formats.py     # SRT/VTT/JSON/TXT 직렬화
├── pipeline.py    # 다운로드+STT+저장 파이프라인
└── cli.py         # 명령줄 인터페이스
webapp/                 # 웹 UI (FastAPI + SSE)
├── server.py      # API 서버 (작업 큐 + 실시간 스트림)
└── static/        # index.html · app.css · app.js
tests/
└── test_formats.py  # 형식 변환 단위 테스트
```

## 테스트

```bash
pip install pytest
pytest
```

## 주의

- 저작권/이용약관을 준수하여 본인이 권한을 가진 영상에만 사용하세요.
- 정확도는 모델 크기와 오디오 품질에 따라 달라집니다. 중요한 용도라면
  `medium` 이상 모델을 권장합니다.
