# Hugging Face Spaces (Docker SDK) 용 이미지.
# 로컬에서도 동일하게 동작한다:  docker build -t sound . && docker run -p 7860:7860 sound
FROM python:3.11-slim

# 오디오 디코딩 안정성을 위한 ffmpeg
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# HF Spaces 는 비루트(uid 1000) 사용자로 실행된다
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH" \
    HOME=/home/user \
    HF_HOME=/home/user/.cache/huggingface \
    SOUND_OUTPUT_DIR=/home/user/app/output/web \
    PYTHONUNBUFFERED=1

WORKDIR /home/user/app

# 의존성 먼저 설치 (레이어 캐시 활용)
COPY --chown=user requirements.txt requirements-web.txt ./
RUN pip install --no-cache-dir --user -r requirements-web.txt

# 앱 코드 복사
COPY --chown=user . .

# HF Spaces 기본 포트
EXPOSE 7860
CMD ["uvicorn", "webapp.server:app", "--host", "0.0.0.0", "--port", "7860"]
