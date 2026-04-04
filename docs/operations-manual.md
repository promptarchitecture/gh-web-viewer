# gh-web-viewer 운영 매뉴얼

이 문서는 현재 `gh-web-viewer`를 다시 켜고, 점검하고, 문제를 찾을 때 보는 실사용 운영 문서입니다.

## 1. 이 시스템이 하는 일

현재 구조는 아래 4개가 연결되어 있습니다.

1. GitHub Pages 공개 프론트
2. Render 공개 API
3. 로컬 Rhino + Grasshopper
4. 로컬 worker

흐름은 이렇게 이해하면 됩니다.

- 웹에서 슬라이더 변경
- Render API에 job 생성
- 로컬 worker가 job을 가져옴
- worker가 로컬 GH 제어 서버로 전달
- Grasshopper 재계산
- 최신 모델/summary를 다시 Render로 업로드
- 웹이 최신 결과를 다시 읽음

## 2. 현재 실사용 주소

### 공개 프론트

- [GitHub Pages 프론트](https://promptarchitecture.github.io/gh-web-viewer/)

### 공개 API

- [Render API Health](https://gh-web-viewer-api.onrender.com/health)
- [Render API Config](https://gh-web-viewer-api.onrender.com/api/config)
- [Render API Controls](https://gh-web-viewer-api.onrender.com/api/controls)
- [Render Published Manifest](https://gh-web-viewer-api.onrender.com/api/published/manifest)
- [Render Published Summary](https://gh-web-viewer-api.onrender.com/api/published/summary)
- [Render Published Model](https://gh-web-viewer-api.onrender.com/api/published/model)

## 3. 핵심 파일 위치

### 프론트

- [rhino-viewer.html](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/web/rhino-viewer.html)
- [rhino-viewer.js](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/web/rhino-viewer.js)
- [rhino-viewer-core.js](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/web/rhino-viewer-core.js)
- [site-config.production.json](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/web/site-config.production.json)

### 공개 API

- [server.py](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/api/server.py)

### 로컬 브리지 / 워커

- [gh_control_server.py](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/scripts/gh_control_server.py)
- [worker.py](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/runner/worker.py)

### 로컬 최신 결과

- [current-preview.3dm](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/output/latest/current-preview.3dm)
- [manifest.json](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/output/latest/manifest.json)
- [summary.json](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/output/latest/summary.json)
- [controls.json](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/output/latest/controls.json)

## 4. 다시 켜는 순서

아래 순서대로 켜면 가장 덜 꼬입니다.

### 1단계. Rhino와 Grasshopper 열기

- Rhino를 열고 작업 대상 `.3dm` 파일을 엽니다.
- Grasshopper를 열고 대상 `.gh` 파일을 엽니다.
- GH 캔버스 안에 게시 컴포넌트가 살아 있는지 확인합니다.

### 2단계. 로컬 GH 제어 서버 켜기

터미널 1:

```bash
python3 /Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/scripts/gh_control_server.py
```

주의:

- `OSError: [Errno 48] Address already in use`가 나오면 이미 켜져 있다는 뜻입니다.
- 이 경우 다시 켤 필요가 없습니다.

### 3단계. 로컬 worker 켜기

터미널 2:

```bash
python3 /Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/runner/worker.py \
  --api-base https://gh-web-viewer-api.onrender.com \
  --local-api-base http://127.0.0.1:8001 \
  --insecure
```

정상 시작 메시지:

```text
Runner polling https://gh-web-viewer-api.onrender.com and forwarding jobs to http://127.0.0.1:8001
```

의미:

- 이 상태면 worker는 job을 기다리는 중입니다.
- 멈춘 것처럼 보여도 정상입니다.

### 4단계. 공개 웹 열기

- [https://promptarchitecture.github.io/gh-web-viewer/](https://promptarchitecture.github.io/gh-web-viewer/) 열기
- 브라우저에서 `Cmd+Shift+R`로 강력 새로고침

### 5단계. 테스트

권장 테스트:

- `최고 높이`를 `81 -> 82`
- 또는 `대지 기부채납 비율`을 작은 폭으로 변경

정상이라면:

- 컨트롤 값이 바뀜
- worker가 job을 처리
- 모델과 SUMMARY가 같이 갱신됨

## 5. 정상 상태 체크리스트

아래가 모두 맞으면 정상입니다.

### Render API

- [health](https://gh-web-viewer-api.onrender.com/health)가 열림
- [api/config](https://gh-web-viewer-api.onrender.com/api/config)에 다음이 보임
  - `controls_api_url`
  - `jobs_api_url`
  - `published_model_url`
  - `published_summary_url`
  - `published_manifest_url`

### 로컬 worker

- worker 터미널이 살아 있음
- SSL 에러 없이 대기 중임

### 공개 프론트

- 왼쪽 `웹 제어 입력` 상태가 `Connected`
- 모델이 뜸
- SUMMARY가 뜸

## 6. 자주 나는 오류와 해결

### A. `Address already in use`

뜻:

- `gh_control_server.py`가 이미 켜져 있음

해결:

- 새로 띄우지 말고 그대로 둠
- worker만 따로 실행

### B. worker에서 `CERTIFICATE_VERIFY_FAILED`

뜻:

- 로컬 Python이 Render HTTPS 인증서를 검증하지 못함

해결:

- worker 실행 시 `--insecure` 사용

```bash
python3 /Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/runner/worker.py \
  --api-base https://gh-web-viewer-api.onrender.com \
  --local-api-base http://127.0.0.1:8001 \
  --insecure
```

### C. 웹에서 `Connected`인데 모델이 안 뜸

먼저 확인:

- [Render Published Model](https://gh-web-viewer-api.onrender.com/api/published/model)

판단:

- 여기서 파일이 내려오면 프론트 쪽 문제일 가능성이 큼
- 404가 나오면 worker 업로드가 안 된 상태

대응:

1. worker를 다시 실행
2. 웹에서 슬라이더를 한 번 바꿔 job 생성
3. 다시 `published/model` 확인

### D. SUMMARY는 바뀌는데 모델은 안 바뀜

뜻:

- summary와 controls는 Render에 올라갔지만
- model 업로드가 실패했거나 늦은 상태

대응:

1. 로컬 [current-preview.3dm](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/output/latest/current-preview.3dm) 파일이 실제로 갱신되는지 확인
2. worker 재시작
3. Render [published/model](https://gh-web-viewer-api.onrender.com/api/published/model) 확인

### E. 모델은 보이는데 `No 3DM model loaded yet.` 문구가 남음

뜻:

- 빈 상태 안내 레이어가 안 숨겨진 UI 문제

상태:

- 이 문제는 [rhino-viewer.js](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/web/rhino-viewer.js)에서 이미 보정했습니다.
- 공개 사이트가 최신 배포로 갱신되면 사라져야 정상입니다.

## 7. 배포를 다시 할 때

### GitHub Pages 프론트 다시 배포

- `main`에 push
- GitHub Actions가 Pages 재배포

관련 문서:

- [github-pages.md](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/docs/github-pages.md)

### Render API 다시 배포

Render에서:

- `Manual Deploy`
- `Deploy latest commit`

관련 문서:

- [render-deployment.md](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/docs/render-deployment.md)

## 8. 지금 시스템의 한계

- Rhino/Grasshopper는 아직 로컬 컴퓨터에 의존합니다.
- worker가 꺼지면 공개 웹의 제어는 멈춥니다.
- Render free 인스턴스는 쉬면 잠들 수 있어서 첫 응답이 느릴 수 있습니다.
- 여러 명이 동시에 제어하면 job 충돌 가능성이 있습니다.

## 9. 나중에 물어보면 내가 기준으로 삼을 문서

앞으로 이 프로젝트에 대해 질문받으면 아래 문서를 우선 기준으로 보면 됩니다.

- [operations-manual.md](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/docs/operations-manual.md)
- [dynamic-deployment.md](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/docs/dynamic-deployment.md)
- [render-deployment.md](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/docs/render-deployment.md)
- [github-pages.md](/Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/docs/github-pages.md)

즉, 나중에 `다시 켜는 법`, `왜 안 되지`, `어디를 봐야 하지`라고 물어보면 이 문서를 기준으로 바로 이어서 답하면 됩니다.
