<!-- 목적: 다음 세션이 이어서 수행할 정답 매핑 테스트(B-002~) 계획과 시작 전 점검 항목. 작성: 2026-10-30 세션 종료 시. 완료한 항목은 체크하고 bench/cases.tsv에 결과를 적는다. -->
# 다음 세션: 정답 매핑 테스트 이어가기

## 0. 시작 전 점검 (이번 세션에서 미확인으로 남은 고리)
- [ ] `.claude/settings.json` env 적용 확인: `go env GOPATH GOCACHE GOMODCACHE`, `npm config get cache`가 `.cache/` 아래인지, `echo $PIP_REQUIRE_VIRTUALENV`가 `true`인지.
- [ ] 프로젝트 메모리 로드 확인: 시스템 프롬프트의 메모리 경로가 `~/.claude/projects/-home-yh-projects-RE-by-leanrea/memory`이고 `MEMORY.md` 내용이 보이는지(심볼릭 링크 -> `.claude/memory/`).
- [ ] 스킬 로드 확인: 스킬 목록에 프로젝트 `leanrea`가 보이는지(전역 사본은 삭제됨).
- [ ] `.REA` 패키지: 사용자가 `requirements.txt`로 설치했는지, `.REA/bin/hbc-decompiler`가 bad interpreter 없이 실행되는지. 아니면 `.claude/CLAUDE.md`의 `-m` 호출을 유지.
- [ ] 위 결과를 이 파일에 체크하고, 실패한 항목은 관측 -> 원인 -> 조치로 `.claude/CLAUDE.md`에 반영.

## 1. 테스트 대상 (추천, 플랫폼·형식 비중복)
소스 공개 여부와 릴리스 바이너리 존재는 이전 세션 지식 기준이라 **추정**이다. 다운로드 전 사용자에게 목록을 알리고, 받은 뒤 태그·sha256을 확인해 확인으로 바꾼다.

| id | 플랫폼 / 형식 | 대상 | 범위(기능 하나) | 이 사례로 검증할 M 항목 |
|---|---|---|---|---|
| B-002 | linux-x86_64 / ELF-C | minisign (jedisct1/minisign) | `-V` 서명 검증: 공개키·`.minisig` 파싱 -> Ed25519 검증 -> trusted comment 검증 | M-003(정적 링크 libsodium 구간의 call 해석) |
| B-003 | linux-x86_64 / ELF-Rust | ripgrep (BurntSushi/ripgrep) | `.gitignore` 규칙 매칭 경로 | M-003, 새 Rust 항목 후보(단형화 함수 식별) |
| B-004 | windows-x86_64 / PE-C | PuTTY `puttygen.exe` 또는 7-Zip `7zr.exe` | 키 생성 또는 7z 헤더 파싱 | M-203(import 호출부), PE 일반 |
| B-005 | android / APK-Kotlin | Aegis Authenticator (F-Droid 재현 빌드) | TOTP 코드 생성(시크릿 -> HMAC -> 6자리) | APK/jadx 경로, 새 항목 후보 |
| B-006 | wasm / WASM-Rust | 공개 WASM 데모 빌드(대상 선정 필요) | export 함수 하나 | WASM 경로, 새 항목 후보 |
| B-007 | linux-x86_64 / ELF-Go(stripped) | age 이외 Go CLI 1개(예: `gh`, `restic`) | 기능 하나 | M-101, M-102, M-103을 추정 -> 확인으로 올릴 2번째 사례 |

권장 순서: B-007(기존 Go 항목 2번째 사례로 바로 확인 가능) -> B-002 -> B-003 -> B-004 -> B-005 -> B-006.

## 2. 사례마다 수행 절차 (루트 CLAUDE.md "정답 매핑 테스트" 요약)
1. 바이너리만 `targets/<name>/`에 받고 sha256·버전 기록. 소스는 `analysis/<name>/src`에 받되 블라인드 분석이 끝날 때까지 열지 않는다.
2. 분석 흐름 0~6 수행, 노트 `notes/<name>/NN-*.md`, 결과물 `targets/<name>/result/NN-*`, 스크립트 `tmp/<name>/`.
3. 소스 대조 채점 `notes/<name>/NN-source-grading.md`: 항목별 맞음/추정 적중/누락/오답 + 근거(소스 파일:줄, 바이너리 주소).
4. `bench/cases.tsv`에 B-NNN 한 줄.
5. 누락·오답마다 METHODS.md 갱신(기존 항목 사례 추가 또는 새 M 항목), 고친 방법으로 해당 고리 재분석해 잡히는지 확인.
6. 분석 완료 선언 후 `tmp/<name>/` 삭제.

## 3. 이번 세션 기준선 (비교용)
- B-001 age: 맞음 9, 추정 적중 2, 누락 5, 오답 0. 누락 원인 3종(간접 호출, bool 분기, 이름만 본 호출).
- METHODS.md: 항목 10개 중 확인 1(M-002), 추정 9.
- 다음 세션의 1차 지표: 사례당 누락 수(기준 5)와 오답 수(기준 0), 추정 -> 확인으로 올라간 M 항목 수.
