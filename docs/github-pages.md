# GitHub Pages 배포

이 프로젝트는 GitHub Pages에서 `dist-static` 폴더를 자동 생성해서 배포하도록 설정되어 있습니다.

## 현재 구성

- 워크플로 파일:
  - `.github/workflows/deploy-pages.yml`
- 정적 번들 생성 스크립트:
  - `scripts/export_static_site.py`
- GitHub Pages에 올라갈 실제 결과물:
  - `dist-static/`

## 배포 방식

1. 저장소를 GitHub에 올립니다.
2. 기본 브랜치를 `main`으로 둡니다.
3. `main` 브랜치에 push 하면 GitHub Actions가 실행됩니다.
4. Actions가 `scripts/export_static_site.py`를 실행합니다.
5. 생성된 `dist-static` 폴더가 GitHub Pages로 배포됩니다.

## GitHub에서 해야 할 설정

1. GitHub 저장소 페이지로 들어갑니다.
2. `Settings`
3. `Pages`
4. `Build and deployment` 항목에서 `Source`를 `GitHub Actions`로 선택합니다.

## 실제 순서

1. GitHub에서 새 저장소를 만듭니다.
2. 이 프로젝트를 그 저장소에 push 합니다.
3. GitHub 저장소에서 `Settings -> Pages -> Source -> GitHub Actions`를 선택합니다.
4. 다시 `main` 브랜치에 push 합니다.
5. `Actions` 탭에서 `Deploy Static Viewer to GitHub Pages`가 성공하는지 확인합니다.
6. 성공하면 `github.io` 주소가 생깁니다.

## 공개 주소

보통 아래 형태로 열립니다.

- `https://<github-username>.github.io/<repository-name>/`

예시:

- `https://promptarchitecture.github.io/gh-web-viewer/`

## 배포 전 확인

배포 전에 최신 결과를 반영하고 싶다면 로컬에서 먼저 실행합니다.

```bash
python3 /Users/cantturnsmacbook/Documents/codex/rhino/gh-web-viewer/scripts/export_static_site.py
```

다만 실제 GitHub Pages 배포는 workflow 안에서 다시 `dist-static`를 생성하므로, 핵심은 다음 파일들이 최신 상태로 커밋되어 있어야 한다는 점입니다.

- `output/latest/current-preview.3dm`
- `output/latest/manifest.json`
- `output/latest/summary.json`
- `output/latest/controls.json`

## 주의

GitHub Pages는 정적 배포입니다.

가능한 것:
- 모델 보기
- Summary 보기
- 컨트롤 UI 보기

불가능한 것:
- Rhino/Grasshopper 실시간 계산 실행
- 로컬 제어 서버 사용

즉 GitHub Pages는 현재 상태를 공유하는 공개 웹페이지 용도입니다.
