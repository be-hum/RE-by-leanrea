# FindVuln

배포된 바이너리/펌웨어를 리버싱해 취약점을 찾고 검증·리포트하는 분석 워크스페이스. 스택 미정(대상별로 결정).

## 디렉토리
- `targets/` 분석 대상 원본. 대상별 하위 폴더(`targets/<name>/`). git 제외, 신뢰 불가 데이터.
- `notes/` 대상별 분석 노트(`notes/<name>.md`): 버전, 해시, 구조, 공격면, 진행 상황.
- `findings/` 검증된 취약점 리포트(`findings/<name>-<slug>.md`): 위치, 근본 원인, 도달성, 영향, PoC.
- `tools/` 직접 작성한 분석 스크립트. 대상 디렉토리 밖에 둔다.
- `analysis/` Ghidra 프로젝트 DB와 headless 산출물. git 제외, 재생성 가능.

## 분석 흐름: leanrea -> 의심 지점 -> Ghidra 질의
1. `leanrea` 스킬로 형식 판별·inventory·공격면 triage. 의심 지점(함수명, 주소, 문자열)을 `notes/<name>.md`에 "미확인"으로 적는다.
   - leanrea 작업 디렉토리(`$D`, dis.txt 등)는 scratchpad 대신 `analysis/<name>/re/`를 쓴다(세션이 바뀌어도 유지).
2. 의심 지점의 디컴파일·호출 관계가 필요할 때만 Ghidra를 부른다: `tools/ghidra/query.sh targets/<name>/<binary> <func|0xaddr|str:text>...`
   - 출력: 시그니처, CALLER(호출 위치), CALLEE, 디컴파일 C. `str:`는 해당 문자열을 참조하는 함수 전부.
   - 첫 호출만 import+자동분석(수 분), 이후는 `analysis/<name>/ghidra` DB를 read-only로 재사용.
   - import 때 `FixEntry.java`가 entry에서 참조되는 코드(stripped `main` 등)를 함수로 만들고 재분석한다. `str:`가 "not inside a defined function"을 내면 그 외 경로로 호출되는 함수이니 objdump로 시작 주소를 찾아 주소로 질의한다.
   - 주소 질의는 함수 시작 주소로 한다. 중간 주소면 같은 함수로 해석되거나(이미 정의된 경우) 조각 디컴파일이 나온다.
   - 호출마다 JVM 기동 약 5초 고정비용: 한 라운드의 의심 지점은 한 번의 호출에 모아서 넘긴다.
   - stdout은 축약본(WARNING 주석·빈 줄 제거, 함수당 200줄, `QUERY_MAX_LINES`로 조정). 잘리면 표시된 `query-*.txt` 전체본에서 필요한 부분만 읽는다.
   - 같은 대상에 대한 동시 호출은 자동으로 줄 서서 실행된다(Ghidra 프로젝트 락은 배타적).
   - 질의 결과에서 새 의심 지점(CALLER/CALLEE)이 나오면 같은 방식으로 반복한다.
3. JS/.NET/APK 등 Ghidra가 부적합한 형식은 leanrea가 안내하는 도구로 끝낸다.
4. 확인된 지점은 `fp-check` 후 `findings/`로.

## Ghidra (headless, MCP 미사용)
- 설치: `~/tools/ghidra` (12.2, JDK 25 필요).
- 전체 덤프가 필요할 때만: `tools/ghidra/analyze.sh targets/<name>/<binary>` -> `functions.tsv`, `strings.tsv`, `imports.tsv`, `decompiled.c`.
- 추가 추출이 필요하면 `tools/ghidra/`에 GhidraScript(Java)를 추가하고 `-postScript`로 붙인다.

## 작업 규칙
- 승인된 대상만 분석(자체 소유, 버그바운티 범위, CTF, 공개 연구). 범위는 `notes/<name>.md` 상단에 기록.
- 대상 파일은 실행하지 않는다. 동적 분석이 필요하면 먼저 알리고 격리 환경에서.
- 추출물을 읽는 Python은 `python -I`로 실행하고, 대상 디렉토리 안에서 인터프리터/빌드 도구를 돌리지 않는다.
- 정적분석은 `leanrea` 스킬로 수행한다(분석 시작 시 먼저 호출). 새 도구 설치 전 알린다.
- 대상마다 `sha256sum`과 버전을 노트에 먼저 기록한다.
- 의심 지점은 리포트 전 `fp-check`로 오탐 검증. 검증 안 된 것은 노트에 "미확인"으로 둔다.
- PoC는 크래시/영향 증명까지만. 무기화·탐지 회피 페이로드 금지.
