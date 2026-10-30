<!-- 목적: "대상 파일은 실행하지 않는다"(루트 CLAUDE.md 1원칙)의 유일한 예외인 함수 단위 에뮬레이션의 트리거, 관문, 승인, 준비·설치, 인터페이스, 결과 처리 절차. 정적으로 풀리지 않는 값 계산 고리가 생기면 에이전트는 이 파일을 직접 읽고 순서대로 시행한다. 생성: tmp-of-edit/06-unified-plan.md 7절(03 4절 + 04 우려 4~10 통합), 2026-10-30. 에뮬 도구(emu.sh, Emulate.java)는 아직 구현하지 않았다(첫 트리거 때 7-2 단계 5에서 구현). -->
# 에뮬레이션 절차 (1원칙의 예외)

## 0. 경계
- 금지(예외 없음): 대상 코드가 호스트 OS 자원(syscall, 파일, 네트워크, 프로세스)에 닿는 모든 실행. 직접 실행, QEMU user, GDB, wine, 샌드박스 실행 포함.
- 허용(이 절차를 거친 경우만): 격리된 메모리 모델 안에서 syscall 통과 없이 함수 하나 또는 연속 구간을 에뮬레이션. 기본 에뮬레이터는 Ghidra 내장 `EmulatorHelper`(`~/tools/ghidra/Ghidra/Framework/Emulation/lib/Emulation.jar`). 경계 기준은 "CPU에서 도는가"가 아니라 "OS 자원에 닿는가"다(JIT 에뮬레이터도 호스트 코드로 번역해 돈다).
- 용도: 정적으로 흐름을 읽은 함수의 출력값 확인. 흐름 해석을 대신하지 않는다(루트 CLAUDE.md 분석 흐름 0).

## 1. 트리거
- 조건: 어떤 고리가 관문 1과 관문 2를 충족한다.
- 조치: 그 고리를 미확인으로 닫기 전에 이 파일을 읽고 아래 순서대로 시행한다. 기억·요약으로 대신하지 않는다.
- 전제 확인(하나라도 없으면 시행하지 않고 사용자에게 알림):
  - `grep -n 'emu.sh' .claude/settings.json`이 `permissions.ask` 항목을 보여 준다.
  - 루트 `CLAUDE.md` 규칙 절에 "OS 자원" 기준 1원칙 문구가 있다.
- 순서: 관문 판단과 기록 -> 준비 점검(4) -> (미비 시) 설치·구현 -> 승인 요청(3) -> 하네스 확인 창 승인 -> 시행 -> 결과 처리(6).

## 2. 관문 (전부 충족, 하나라도 아니면 그 고리는 미확인)
1. **정적 소진:** 같은 고리를 서로 다른 방법(다른 M 항목 또는 다른 도구) 3회로 시도했고, 각 시도의 방법과 막힌 지점이 노트에 있다. 같은 방법 반복은 1회로 센다.
2. **막힌 원인이 계산량:** 흐름은 읽었으나 값 계산이 어렵다(디코더 루프, 복호 테이블, 상수 생성). 흐름 자체가 미확인이면 해당 없음. 패킹 해제 스텁이면 루트 CLAUDE.md 분석 흐름 2의 `upx -d`와 변조 복원 실패 기록이 먼저 있어야 한다.
3. **닫힌 범위:** 함수 하나 또는 연속 구간. 범위 안 callee 목록을 적고, 범위 밖의 모든 callee(import, syscall, 간접 호출, 할당자, 런타임, 정적 링크 libc)는 없거나, 동작이 정적으로 확인되어 값만 돌려주는 스텁으로 대체할 수 있다.
4. **입력 근거:** 값 자체(키, 설정값)를 묻는 고리는 레지스터·메모리 초기값마다 정적 근거(주소, result 파일 줄)가 있다. 변환의 정체(예: 이 함수가 SHA-256인가)를 묻는 고리만 공개 테스트 벡터 같은 합성 입력을 허용하고 `synthetic`으로 표시한다.
5. **사전 기대:** 시행 전에 "무엇이 나오면 어느 고리가 확인되는가", 정지 주소, `max` 스텝을 적는다. 결과를 보고 질문을 바꾸지 않는다. 계산·탐색 방식(입력 탐색 순서, 선택 기준, 유일성 점검)도 시행 전에 적는다. 시행 중 방식을 바꾸거나 점검을 덧붙이려면 판단 기록에 변경을 남기고 3절의 새 승인 요청을 한다(관측: 2026-10-31 Twist1에서 탐색 방식을 두 번 바꾸고 sweep을 추가함).
- 기록: `notes/<name>/NN-emulation-gate.md`에 관문 1~5를 "충족(근거) / 미충족"으로 쓴다.

## 3. 승인 요청
시행 전에 사용자에게 한 번에 보여 준다.
```
에뮬 승인 요청: <name> / <bin> (sha256 앞 12자)
고리: <노트 단계와 미확인 고리 한 줄>
관문: 1 <방법 3종> / 2 <무엇을 계산> / 3 <함수 주소, 범위 밖 callee 처리> / 4 <입력과 근거 또는 synthetic> / 5 <기대 형식, stop, max>
에뮬레이터: <Ghidra EmulatorHelper | Unicorn>, 준비: <4절 결과>
판단 기록: notes/<name>/NN-emulation-gate.md
```
- 실제 승인은 `emu.sh`/`unicorn_run.py` 호출 시 뜨는 하네스 확인 창이다(`.claude/settings.json` `permissions.ask`). 대화 중 승인은 확인 창을 대신하지 않는다. 단 `~/.claude/settings.json`의 `defaultMode`가 `auto`이면 확인 창이 뜨지 않을 수 있다(관측: 2026-10-31 Twist1에서 확인 창이 떴다는 기록이 없었음). 그 경우 확인 창이 떴다고 쓰지 않고, 요청 글을 보인 뒤 사용자 응답을 기다려 그 응답을 승인으로 기록한다.
- 승인 요청 글을 쓴 같은 턴에 시행하지 않는다(관측: 2026-10-31 Twist1 4회 시행이 사용자 응답 없이 진행됨).
- 범위: 요청에 적은 함수·입력·stop·max 조합만. 재시도 조합도 미리 적지 않았으면 새로 요청한다.
- 승인 후 에이전트가 판단 기록 끝에 `승인: YYYY-MM-DD, 범위: <조합>`을 쓴다. 러너(`emu.sh`, `unicorn_run.py`)는 같은 범위 줄이 없으면 시행하지 않고 거부한다(러너가 스스로 줄을 쓰지 않는다).
- 거절되면 고리를 미확인으로 닫고, 그 고리에 의존하는 결론은 빼거나 조건부로 쓴다.

## 4. 준비 점검과 설치 순서
위에서부터 점검하고, 실패한 단계의 조치를 끝낸 뒤 그 단계부터 다시 점검한다. 모두 통과해야 3절로 간다.

| 단계 | 점검 | 통과 조건 | 실측(2026-10-30) | 미비 시 |
|---|---|---|---|---|
| 1 JDK | `java -version` | Ghidra `application.java.min` 이상 | 통과: OpenJDK 25.0.4.1, 요구 25 | 사용자에게 `! sudo apt install openjdk-25-jdk` 요청 |
| 2 Ghidra | `ls ~/tools/ghidra/support/analyzeHeadless`; `grep application.version ~/tools/ghidra/Ghidra/application.properties` | 존재, 버전 기록 | 통과: 12.2 | 아래 "Ghidra 설치" |
| 3 에뮬 클래스 | `unzip -l ~/tools/ghidra/Ghidra/Framework/Emulation/lib/Emulation.jar \| grep EmulatorHelper.class` | 1행 이상 | 통과 | 단계 2로 재설치 |
| 4 아키텍처 | `ls ~/tools/ghidra/Ghidra/Processors/<arch>/data/languages/*.sla` | `.sla` 존재 | 대상마다 | `~/tools/ghidra/support/sleigh -a <languages 디렉터리>`. 프로세서가 없으면 Unicorn 경로 |
| 5 프로젝트 도구 | `ls tools/ghidra/emu.sh tools/ghidra/Emulate.java` | 존재 | 미구현(Unicorn 경로로 `tools/emu/unicorn_run.py` + `profiles/twist1.py` 구현, Twist1에서 첫 시행 2026-10-31, unicorn 2.1.4 설치 확인) | 5절 인터페이스대로 구현(`Emulate.java`는 opus, `emu.sh`는 sonnet에 위임, model 명시). 첫 구현에서 `-readOnly` DB 위 동작과 `query.sh` flock 공유를 확인 |
| 6 스모크 테스트 | 정적으로 이미 확인한 값 1건을 `emu.sh`로 재현 | 값 일치, status=STOP@지정 주소 | Unicorn 경로 통과(2026-10-31, Twist1 0x407405-0x407423: watch `5200`, STOP@0x407423, steps=8, MAPCHECK ok; 기록 notes/Twist1/02-emulation-gate.md). Ghidra emu.sh 경로는 미수행 | 디코딩 상수가 기록된 기존 노트(예: CRC1, CRC2, SimpleVM)에서 고른다. 처음 한 번도 3절 승인 필요 |
| 7 기록 | `.claude/CLAUDE.md` 도구 절 | 종류·버전·점검일 | 미기재 | `(verified YYYY-MM-DD)`로 추가 |

Ghidra 설치(단계 2·3 실패 시):
1. 외부 다운로드(github.com/NationalSecurityAgency/ghidra/releases), 버전, `~/tools/ghidra` 링크 교체 여부를 알리고 승인 후 진행.
2. 빈 디렉터리 `~/tools/dl-ghidra-<ver>/`에 받고 릴리스에 게시된 SHA-256과 대조(게시가 없으면 GitHub API asset digest로 대조). 다르면 중단.
3. `~/tools/`에 해제. 기존 버전은 지우지 않는다. 링크 교체 전 `readlink -f ~/tools/ghidra`를 기록하고 알린다.
4. 새 버전의 `application.java.min`으로 단계 1부터 재점검.
5. 버전이 바뀌면 `analysis/<name>/ghidra` DB는 업그레이드되어 되돌릴 수 없을 수 있다(추정). 필요하면 stamp를 지우고 재import.

Unicorn 경로(Ghidra 미지원 아키텍처, 또는 Ghidra 에뮬이 같은 관측으로 2회 실패했을 때만):
1. 실패 관측을 노트에 기록.
2. `requirements.txt`에 `unicorn==<버전>`을 추가하고 알린다(2026-10-31 완료: unicorn==2.1.4). 설치는 사용자가 `! .REA/bin/pip install unicorn`(shebang은 2026-10-31에 `.REA` 경로로 고쳐 사용 가능, 이전에는 옛 FindVuln 경로라 `.REA/bin/python -m pip`만 가능했다).
3. `.REA/bin/python -I -c 'import unicorn; print(unicorn.__version__)'`로 확인.
4. `tools/emu/unicorn_run.py` 구현: `emu.sh`와 같은 인자·출력·승인 기록 검사. 바이트 매핑은 `readelf -l`/PE 섹션 offset으로 하고 세그먼트 offset과 대조해 검증.
5. 단계 6 스모크 테스트를 다시 통과한 뒤 사용.

## 5. 인터페이스와 출력
```
tools/ghidra/emu.sh <gate.md> targets/<name>/<bin> <func_addr> max=N [reg=val ...] [mem=addr:hex|@file ...] [stop=addr,...] [watch=addr:len ...] [preset=go-regabi]
```
- 첫 인자는 판단 기록 경로(필수, `승인:` 줄 없으면 거부). `max` 필수, 기본값 없음.
- `preset=go-regabi`: r14에 가짜 g 구조체(stackguard=0)를 둬서 Go 진입부 `cmp rsp,[r14+0x10]`(restic, notes/restic/01-overview.md:13)가 `runtime.morestack`로 빠지지 않게 한다.
- syscall은 항상 정지(EXTCALL). 스텁은 값만 돌려주고 호스트 자원을 쓰지 않는다.
- 원본 전체: `analysis/<name>/<bin>/emu-*.txt`(블록 실행 순서, 모든 메모리 쓰기). 근거로 쓰는 값은 `targets/<name>/result/NN-emu-<설명>.txt`로 복사하고 머리 주석에 입력 인자.
- stdout 요약:
```
EMU func=<addr> status=<STOP@addr | CAP | EXTCALL@addr->name | FAULT@addr reason> steps=<n>
BLOCKS unique=<n> first10=<addr...> (전체: emu-*.txt L<a>-L<b>)
REGS changed: <reg old->new, ...>
MEMDIFF <addr>+<len>: <hex> |<ascii, 비출력은 .>|   (watch 우선, 구간 상한 K, 생략 수 표시)
FILTER rules=<규칙> dropped=<버린 행 수>
```
- MEMDIFF는 hex를 항상 출력(키는 대개 비출력 바이트). 필터는 규칙과 버린 수를 함께 출력(M-005).

## 6. 결과 처리와 사후 점검
- `STOP@<지정 주소>`이고 기대 형식과 맞으면 "에뮬 관측"으로 기록(`.claude/CLAUDE.md` 근거 표기). 가능하면 손으로 1~2 스텝 따라간 값과 대조해 확인으로 올린다.
- CAP, EXTCALL, FAULT는 미확인. 인자 변경 재시도는 2회까지(각각 승인 범위 안), 그 뒤 미확인으로 닫는다.
- 에뮬 결과는 그 고리만 확인한다. 주변 흐름까지 확인했다고 쓰지 않는다.
- 정답 매핑 채점 때 에뮬을 쓴 고리는 "정적으로 풀 수 있었는가"를 따로 판정한다. 풀 수 있었던 경우가 쌓이면 해당 M 항목과 관문 1을 강화한다. 에뮬 첫 사용 시 METHODS.md에 새 M 항목을 만든다.
