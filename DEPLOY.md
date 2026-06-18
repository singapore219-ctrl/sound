# 모바일에서 테스트하기 — Hugging Face Spaces 배포

휴대폰만으로 공개 URL(예: `https://이름-sound.hf.space`)을 만들어 바로 접속해 볼 수 있습니다.
한 번만 설정해두면, 이후 코드가 바뀔 때마다 **GitHub이 자동으로 HF에 올려줍니다.**

준비물: 휴대폰 브라우저, GitHub 계정(이미 있음), Hugging Face 계정(무료).

---

## 1단계 · Hugging Face Space 만들기 (1분)

1. https://huggingface.co/new-space 접속 (없으면 무료 가입)
2. 입력값:
   - **Owner**: 본인 계정 (이 이름이 곧 `HF_USERNAME`)
   - **Space name**: `sound`
   - **SDK**: **Docker** 선택 (중요)
   - **Hardware**: `CPU basic · free`
   - 공개/비공개: 아무거나
3. **Create Space** → 빈 Space가 생깁니다. (아직 비어 있어도 정상)

## 2단계 · HF 액세스 토큰 발급 (1분)

1. https://huggingface.co/settings/tokens 접속
2. **Create new token** → 권한 **Write** 선택 → 생성 → 토큰 문자열 복사
   (한 번만 보이니 복사해두세요)

## 3단계 · GitHub에 토큰/이름 등록 (2분)

GitHub 저장소(`singapore219-ctrl/sound`)의 **Settings → Secrets and variables → Actions** 에서:

- **Secrets** 탭 → **New repository secret**
  - Name: `HF_TOKEN` / Value: (2단계에서 복사한 토큰)
- **Variables** 탭 → **New repository variable**
  - Name: `HF_USERNAME` / Value: (1단계의 본인 HF 계정 이름)
  - (선택) Name: `HF_SPACE` / Value: `sound`  ← Space 이름을 바꿨을 때만

## 4단계 · 자동 배포 실행

위 설정만 끝나면, 이 브랜치에 다음 커밋이 푸시될 때 자동으로 배포됩니다.
**지금 바로 돌리려면** GitHub 저장소 → **Actions** 탭 →
"Deploy to Hugging Face Space" → **Run workflow** 를 누르세요. (모바일 브라우저에서 가능)

배포가 끝나면 Space 페이지에서 빌드 로그가 돌고, 잠시 후
`https://<HF계정>-sound.hf.space` 에서 화면이 뜹니다. 휴대폰에서 그 주소로 접속하면 됩니다.

---

## ⚠️ 알아두기

- **첫 접속 시 모델 다운로드**: 처음 받아쓰기를 누르면 Whisper 모델을 내려받느라
  수십 초 걸릴 수 있습니다(이후엔 빠름). 무료 CPU에선 `tiny`/`base` 모델을 권장합니다.
- **YouTube 차단 가능성**: HF 같은 클라우드 서버 IP는 YouTube가 가끔
  "로봇 확인"으로 막습니다. 이 경우 다운로드가 실패할 수 있는데, 그땐
  파일 업로드 방식(직접 오디오 올리기)을 추가하면 우회됩니다 — 필요하면 말씀해 주세요.
- **무료 Space 절전**: 일정 시간 미사용 시 잠자기(sleep) 상태가 되고, 다시
  접속하면 깨어나는 데 잠깐 걸립니다.
