// sound — 프론트엔드 로직
const $ = (sel) => document.querySelector(sel);

const form = $("#form");
const urlInput = $("#url");
const submitBtn = $("#submit");
const btnLabel = submitBtn.querySelector(".btn-label");
const spinner = submitBtn.querySelector(".spinner");

const resultEl = $("#result");
const statusDot = $("#status-dot");
const statusText = $("#status-text");
const metaEl = $("#meta");
const transcriptEl = $("#transcript");
const downloadsEl = $("#downloads");
const dlButtons = $("#dl-buttons");

const tabs = document.querySelectorAll(".tab");
const panels = document.querySelectorAll(".panel");
const fileInput = $("#file");
const dropzone = $("#dropzone");
const fileInfo = $("#file-info");

let currentSource = null;
let currentJobId = null;
let mode = "youtube";
let selectedFile = null;

// ---- 탭 전환 ----
tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    mode = tab.dataset.mode;
    tabs.forEach((t) => t.classList.toggle("active", t === tab));
    panels.forEach((p) => (p.hidden = p.dataset.panel !== mode));
  });
});

// ---- 파일 선택 / 드래그&드롭 ----
fileInput.addEventListener("change", () => setFile(fileInput.files[0]));

["dragenter", "dragover"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  })
);
["dragleave", "drop"].forEach((ev) =>
  dropzone.addEventListener(ev, (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
  })
);
dropzone.addEventListener("drop", (e) => {
  const f = e.dataTransfer.files[0];
  if (f) setFile(f);
});

function setFile(f) {
  selectedFile = f || null;
  if (!f) {
    fileInfo.hidden = true;
    return;
  }
  const mb = (f.size / (1024 * 1024)).toFixed(1);
  fileInfo.textContent = `📄 ${f.name} · ${mb} MB`;
  fileInfo.hidden = false;
}

function fmtTime(sec) {
  if (sec == null) return "0:00";
  const s = Math.floor(sec % 60);
  const m = Math.floor(sec / 60) % 60;
  const h = Math.floor(sec / 3600);
  const mm = String(m).padStart(h ? 2 : 1, "0");
  const ss = String(s).padStart(2, "0");
  return h ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

function setBusy(busy) {
  submitBtn.disabled = busy;
  spinner.hidden = !busy;
  btnLabel.textContent = busy ? "처리 중…" : "받아쓰기 시작";
}

function setStatus(text, state) {
  statusText.textContent = text;
  statusDot.className = "dot" + (state ? " " + state : "");
}

function selectedFormats() {
  return [...document.querySelectorAll(".chip input:checked")].map((c) => c.value);
}

function reset() {
  if (currentSource) currentSource.close();
  transcriptEl.innerHTML = "";
  metaEl.innerHTML = "";
  downloadsEl.hidden = true;
  dlButtons.innerHTML = "";
  const oldErr = resultEl.querySelector(".error-box");
  if (oldErr) oldErr.remove();
}

function showError(msg) {
  setBusy(false);
  setStatus("오류", "err");
  const box = document.createElement("div");
  box.className = "error-box";
  box.textContent = "⚠ " + msg;
  transcriptEl.after(box);
}

form.addEventListener("submit", (e) => {
  e.preventDefault();

  const formats = selectedFormats();
  if (formats.length === 0) {
    alert("출력 형식을 하나 이상 선택하세요.");
    return;
  }

  let request;
  if (mode === "youtube") {
    const url = urlInput.value.trim();
    if (!url) {
      alert("유튜브 URL 을 입력하세요.");
      return;
    }
    request = fetch("/api/transcribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url,
        model: $("#model").value,
        language: $("#language").value || null,
        device: $("#device").value,
        formats,
      }),
    });
  } else {
    if (!selectedFile) {
      alert("변환할 파일을 선택하세요.");
      return;
    }
    const fd = new FormData();
    fd.append("file", selectedFile);
    fd.append("model", $("#model").value);
    fd.append("language", $("#language").value);
    fd.append("device", $("#device").value);
    fd.append("formats", formats.join(","));
    request = fetch("/api/upload", { method: "POST", body: fd });
  }

  reset();
  resultEl.hidden = false;
  setBusy(true);
  setStatus("작업을 시작하는 중…", "busy");
  resultEl.scrollIntoView({ behavior: "smooth", block: "start" });

  request
    .then((r) => r.json())
    .then((data) => {
      if (data.error) {
        showError(data.error);
        return;
      }
      currentJobId = data.job_id;
      listen(data.job_id);
    })
    .catch((err) => showError("서버 요청 실패: " + err.message));
});

function listen(jobId) {
  const src = new EventSource(`/api/stream/${jobId}`);
  currentSource = src;

  src.onmessage = (e) => {
    const ev = JSON.parse(e.data);
    switch (ev.type) {
      case "status":
        setStatus(ev.message, "busy");
        break;
      case "meta":
        renderMeta(ev);
        break;
      case "segment":
        addSegment(ev);
        break;
      case "done":
        finish(jobId, ev);
        break;
      case "error":
        showError(ev.message);
        src.close();
        break;
    }
  };

  src.onerror = () => {
    // 정상 종료 시에도 onerror 가 호출될 수 있으므로 진행 중일 때만 처리
    if (submitBtn.disabled) {
      setStatus("연결이 종료되었습니다.", "err");
      setBusy(false);
    }
    src.close();
  };
}

function renderMeta(ev) {
  const bits = [];
  if (ev.title) bits.push(`<span><b>${escapeHtml(ev.title)}</b></span>`);
  if (ev.duration) bits.push(`<span>길이 ${fmtTime(ev.duration)}</span>`);
  if (ev.uploader) bits.push(`<span>${escapeHtml(ev.uploader)}</span>`);
  metaEl.innerHTML = bits.join("");
}

function addSegment(ev) {
  const div = document.createElement("div");
  div.className = "seg";
  div.innerHTML =
    `<span class="ts">${fmtTime(ev.start)}</span>` +
    `<span class="txt"></span>`;
  div.querySelector(".txt").textContent = ev.text;
  transcriptEl.appendChild(div);
  // 사용자가 위로 스크롤하지 않았다면 자동 따라가기
  const nearBottom =
    transcriptEl.scrollHeight - transcriptEl.scrollTop - transcriptEl.clientHeight < 80;
  if (nearBottom) transcriptEl.scrollTop = transcriptEl.scrollHeight;
}

function finish(jobId, ev) {
  setBusy(false);
  const langMap = { ko: "한국어", en: "English", ja: "日本語", zh: "中文" };
  const lang = langMap[ev.language] || ev.language;
  setStatus(
    `완료 · ${ev.num_segments}개 구간 · 언어 ${lang}` +
      (ev.language_probability ? ` (${Math.round(ev.language_probability * 100)}%)` : ""),
    "ok"
  );

  dlButtons.innerHTML = "";
  (ev.formats || []).forEach((fmt) => {
    const a = document.createElement("a");
    a.className = "dl-btn";
    a.href = `/api/download/${jobId}/${fmt}`;
    a.textContent = "↓ " + fmt.toUpperCase();
    dlButtons.appendChild(a);
  });
  downloadsEl.hidden = false;
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}
