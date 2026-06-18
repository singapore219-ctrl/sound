# 집 PC에서 24시간 실행 → 모바일에서 유튜브 텍스트화

클라우드(HF 등)는 유튜브가 IP를 차단하지만, **집/사무실 PC는 일반 가정용 IP**라
유튜브 다운로드가 정상 동작합니다. 그 PC에서 앱을 띄우고, 터널로 외부에 열면
**휴대폰에서 어디서든** 유튜브 링크로 받아쓰기를 할 수 있습니다.

```
[휴대폰] ──인터넷──▶ [터널] ──▶ [집 PC의 앱] ──유튜브 다운로드(가정용 IP)──▶ 변환
```

준비물: 늘 켜져 있는 PC(Windows/Mac/Linux), [Docker](https://docs.docker.com/get-docker/) 설치.

---

## 1. 앱 실행 (자동 재시작)

저장소를 받은 폴더에서:

```bash
docker compose up -d --build
```

- 같은 Wi-Fi의 다른 기기(휴대폰 포함)에서 접속: `http://<PC의 내부IP>:8000`
  - PC 내부 IP 확인: Windows `ipconfig`, Mac/Linux `ifconfig` 또는 `ip addr`
  - 예: `http://192.168.0.12:8000`
- `--restart unless-stopped` 라서 PC를 켜두면 부팅 후에도 자동으로 다시 뜹니다.
- 모델은 첫 사용 때 한 번만 내려받고 이후 캐시(`hf-cache` 볼륨)에 보존됩니다.

> 집 안에서만 쓰면 여기까지로 충분합니다. **밖에서도** 쓰려면 아래 2번.

## 2. 모바일에서 어디서든 접속 (공개 URL)

### 방법 A — Cloudflare 빠른 터널 (가장 쉬움, 계정 불필요) ⭐

```bash
docker compose --profile tunnel up -d --build
docker compose logs tunnel        # 출력에서 https://xxxxx.trycloudflare.com 확인
```

그 주소를 휴대폰 브라우저에서 열면 끝. (단, 터널 컨테이너를 재시작하면 주소가
바뀝니다. 고정 주소가 필요하면 방법 B.)

### 방법 B — Cloudflare 명명형 터널 (고정 주소, 무료 / 본인 도메인 필요)

1. Cloudflare 계정 + 도메인 등록 → Zero Trust → Tunnels 에서 터널 생성
2. 발급된 토큰으로 실행:
   ```bash
   docker run -d --restart unless-stopped --network sound_default \
     cloudflare/cloudflared:latest tunnel --no-autoupdate run --token <토큰>
   ```
   public hostname 의 service 를 `http://sound:7860` 으로 지정.

### 방법 C — Tailscale (비공개, 가장 안전)

PC와 휴대폰에 [Tailscale](https://tailscale.com/) 설치 후 같은 계정으로 로그인.
휴대폰에서 `http://<PC의 Tailscale 이름>:8000` 으로 접속. 공개 노출이 전혀 없어
개인용으로 가장 안전합니다.

---

## ⚠️ 보안 메모

- 방법 A/B는 URL을 아는 사람이면 누구나 접속할 수 있습니다(주소는 무작위라 추측은
  어렵지만 공개됨). 개인용이면 **방법 C(Tailscale)** 또는 Cloudflare Access 인증
  추가를 권장합니다.
- 이 앱은 입력한 유튜브를 **그 PC에서** 내려받아 변환합니다. 본인이 권한을 가진
  영상에만 사용하세요.

## Docker 없이 실행하려면

```bash
pip install -r requirements-web.txt
HOST=0.0.0.0 PORT=8000 python -m webapp      # 0.0.0.0 이어야 다른 기기에서 접속됨
```

자동 재시작은 OS의 서비스(systemd / Windows 작업 스케줄러 등)로 등록하세요.
