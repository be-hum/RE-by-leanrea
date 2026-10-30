<!-- 목적: 다음 세션이 이어서 수행할 정답 매핑 테스트(B-002~) 계획과 시작 전 점검 항목. 작성: 2026-10-30 세션 종료 시. 완료한 항목은 체크하고 bench/cases.tsv에 결과를 적는다. -->
# 다음 세션: 정답 매핑 테스트 이어가기

## 0. 시작 전 점검 (이번 세션에서 미확인으로 남은 고리)
- [x] `.claude/settings.json` env 적용 확인: `go env GOPATH GOCACHE GOMODCACHE`, `npm config get cache`가 `.cache/` 아래인지, `echo $PIP_REQUIRE_VIRTUALENV`가 `true`인지. (2026-10-30 확인: GOPATH=.cache/go, GOCACHE=.cache/go-build, GOMODCACHE=.cache/go/pkg/mod, npm cache=.cache/npm, PIP=true)
- [x] 프로젝트 메모리 로드 확인: 시스템 프롬프트의 메모리 경로가 `~/.claude/projects/-home-yh-projects-RE-by-leanrea/memory`이고 `MEMORY.md` 내용이 보이는지(심볼릭 링크 -> `.claude/memory/`). (확인: 링크 정상, 세션 컨텍스트에 MEMORY.md 로드됨)
- [x] 스킬 로드 확인: 스킬 목록에 프로젝트 `leanrea`가 보이는지(전역 사본은 삭제됨). (확인: 스킬 목록에 leanrea 있음, `~/.claude/skills/`에 전역 사본 없음)
- [x] `.REA` 패키지: 사용자가 `requirements.txt`로 설치했는지, `.REA/bin/hbc-decompiler`가 bad interpreter 없이 실행되는지. 아니면 `.claude/CLAUDE.md`의 `-m` 호출을 유지. (확인: pefile 2024.8.26, hermes-dec 0.1.8 설치됨. `.REA/bin/hbc-decompiler`는 여전히 bad interpreter(FindVuln shebang) -> `-m` 호출 유지, 해당 호출은 정상 동작)
- [x] 위 결과를 이 파일에 체크하고, 실패한 항목은 관측 -> 원인 -> 조치로 `.claude/CLAUDE.md`에 반영. (실패 항목 없음: 기존 `-m` 조치가 그대로 유효해 CLAUDE.md 변경 불필요)

## 1. 테스트 대상 (추천, 플랫폼·형식 비중복)
소스 공개 여부와 릴리스 바이너리 존재는 이전 세션 지식 기준이라 **추정**이다. 다운로드 전 사용자에게 목록을 알리고, 받은 뒤 태그·sha256을 확인해 확인으로 바꾼다.

| id | 플랫폼 / 형식 | 대상 | 범위(기능 하나) | 이 사례로 검증할 M 항목 |
|---|---|---|---|---|
| B-002 (완료 2026-10-30, minisign 0.12, notes/minisign/04-source-grading.md; 실측: C + Zig(libzodium) 정적 빌드로 계획의 libsodium 가정은 틀림) | linux-x86_64 / ELF-C | minisign (jedisct1/minisign) | `-V` 서명 검증: 공개키·`.minisig` 파싱 -> Ed25519 검증 -> trusted comment 검증 | M-003(정적 링크 libsodium 구간의 call 해석) |
| B-003 (완료 2026-10-30, ripgrep 15.2.0) | linux-x86_64 / ELF-Rust | ripgrep (BurntSushi/ripgrep) | `.gitignore` 규칙 매칭 경로 | M-003, 새 Rust 항목 후보(단형화 함수 식별) |
| B-004 (완료 2026-10-30, 7zr.exe 26.05 (7-Zip)) | windows-x86_64 / PE-C | PuTTY `puttygen.exe` 또는 7-Zip `7zr.exe` | 키 생성 또는 7z 헤더 파싱 | M-203(import 호출부), PE 일반 |
| B-005 (완료 2026-10-30, Aegis v3.4.3) | android / APK-Kotlin | Aegis Authenticator (F-Droid 재현 빌드) | TOTP 코드 생성(시크릿 -> HMAC -> 6자리) | APK/jadx 경로, 새 항목 후보 |
| B-006 (완료 2026-10-30, dprint-plugin-json 0.25.2) | wasm / WASM-Rust | 공개 WASM 데모 빌드(대상 선정 필요) | export 함수 하나 | WASM 경로, 새 항목 후보 |
| B-007 (완료 2026-10-30, restic 0.19.1, notes/restic/04-source-grading.md) | linux-x86_64 / ELF-Go(stripped) | age 이외 Go CLI 1개(예: `gh`, `restic`) | 기능 하나 | M-101, M-102, M-103을 추정 -> 확인으로 올릴 2번째 사례 |

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

## 4. 완료 결과 (2026-10-30, B-001~B-007 전부 수행)
| id | 대상 | 맞음 | 추정 적중 | 누락 | 오답 |
|---|---|---|---|---|---|
| B-001 | age (Go PIE) | 9 | 2 | 5 | 0 |
| B-007 | restic (Go non-PIE) | 9 | 3 | 5 | 2 |
| B-002 | minisign (C+Zig, ELF) | 9 | 3 | 4 | 3 |
| B-003 | ripgrep (Rust, ELF) | 12 | 2 | 6 | 0 |
| B-004 | 7zr.exe (PE32) | 10 | 5 | 4 | 0 |
| B-005 | Aegis (APK) | 10 | 2 | 0 | 0 |
| B-006 | dprint-plugin-json (WASM) | 9 | 4 | 0 | 0 |
| 합계 | 118항목 | 68 | 21 | 24 (20%) | 5 (4%) |

- 형식별: 네이티브 ELF/PE(Go, C, Rust, PE) 누락 4~6, 오답 0~3. APK(jadx)·WASM(name 섹션 보존)은 누락 0, 오답 0이지만 난이도가 낮은 범위라 직접 비교하지 않는다.
- 누락 24건 원인 빈도: (1) 분기 목적지·비교 인자·옵션 호출 미해석(M-003) 17건 71%, (2) 범위 후반 단계 담당 함수 미식별(M-008) 7건 29%.
- 오답 5건 원인: 오류 문자열-조건 귀속 오류 2(M-004), 함수 역할 오귀속 1(M-206), 서드파티 구현체 단정 1(M-207), 단계 순서 서술 1.
- M 항목: 추정 -> 확인으로 올라간 것 M-003, M-008, M-101, M-102, M-103, M-206. 새 항목 M-004, M-005, M-008, M-104, M-205, M-207, M-209, M-301, M-401, M-501(전부 사례 1건이라 추정).
- 재사용 스크립트는 `tools/scripts/`(gosym-funcs, ann.py, strann.py, fn.py)로 옮겼다. `tmp/<name>/`은 삭제.

## 4-2. M-008 재분석 결과 (2026-10-30, 소스를 본 뒤의 재분석이라 블라인드 성적 아님)
| 대상 | 재분석 대상 누락 | 위치까지 잡힘 | 부분 | 미수행 |
|---|---|---|---|---|
| 7zr | 1~4 (NextHeader 정합성, 크기 0, 버전, CRC·범위) | 4 | 0 | 0 |
| ripgrep | 1~4, 6 | 1(마지막 일치 우선), 3(체인 구조) | 2(is_dir=false만), 4(옵션 값 구조, 이름 대응 추정) | 6 |
| restic | 2 (ErrUnauthenticated 전역) | 1 | 0 | 0 |
| minisign | 2, 4 | 2 | 0 | 1, 3 |
- 가장 효과적인 앵커: 고유 필드 오프셋(7zr), 패닉 Location 줄 번호(ripgrep), 초기화·사용 주소 일치(restic), `cmove` 후보 주소(minisign). 노트: `notes/<name>/05-reanalysis.md`.
- 한계: 모든 재분석은 소스를 본 뒤 수행. M-008의 블라인드 효과는 새 대상(예: B-008)에서 "범위 항목별 앵커 목록 먼저 작성"을 지키고 누락이 줄어드는지로만 확인 가능.

## 4-3. M-008 블라인드 검증 (B-008 zoxide, B-009 xz.exe, 2026-10-30)
- 설계: 소스를 열기 전에 `notes/<name>/00-anchors.md`로 범위 단계(S1~S5, X1~X5)와 앵커 후보, 채점 규칙, 판정 기준(누락 2 이하 유효, 3~4 불확실, 5 이상 효과 없음)을 확정.
| id | 대상 | 맞음 | 추정 적중 | 누락 | 오답 | 담당 함수를 못 찾은 단계 | 판정 |
|---|---|---|---|---|---|---|---|
| B-008 | zoxide (Rust ELF) | 12 | 4 | 6 | 0 | 0/5 | 효과 없음(누락 6) |
| B-009 | xz.exe (PE32+) | 9 | 5 | 3 | 0 | 2/5 | 효과 불확실(누락 3) |
- 결론: M-008은 "담당 함수 식별" 누락을 줄였다(이전 사례 ripgrep·7zr에서는 누락의 상당수). 그러나 총 누락은 기준선(4~6)을 확실히 낮추지 못했다. 남은 누락의 대부분은 찾은 함수 안의 분기·기본값·건너뜀/오류 종료 구분 미해석(M-003 유형).
- 후속 가설(미검증): "문자열 참조 지점마다 그 앞 조건 분기와 결과(건너뜀/오류/계속)를 한 줄로 쓴다"를 M-003 체크리스트에 넣으면 누락이 줄어든다. 다음 사례(B-010 이후)에서 시험.

## 4-4. 전체 집계 (B-001~B-009, 9건 157항목)
- 맞음 89, 추정 적중 30, 누락 33(21%), 오답 5(3%). 네이티브 7건만: 누락 33/132(25%), 오답 5(4%). APK·WASM(누락 0)은 난이도가 낮아 제외 비교 필요.
- M 항목 상태: 확인 = M-002, M-003, M-008(함수 식별에 한정), M-101, M-102, M-103, M-206, M-301. 나머지(M-001, M-004, M-005, M-104, M-201~M-205, M-207~M-209, M-401, M-501)는 사례 1건 또는 방식 불일치로 추정.

## 5. 미완료·후속
- 재분석 후에도 미확인: ripgrep 누락 6(`is_absolute`, `any_git`) 및 2·4의 나머지, minisign 누락 1·3(공개키 파일 1행 무시, `trim`).
- 약한 사례: Aegis(RFC 알고리즘, jadx 소스 근접), dprint(name 섹션 보존). 후속으로 Aegis 볼트 복호화(scrypt+AES-GCM)나 name 섹션 제거 WASM을 범위로 추가.
- 출처 진위(서명·체크섬) 미확인: minisign, 7zr, Aegis, dprint는 릴리스 체크섬 없음.
