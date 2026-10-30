# leanrea 운영 규칙 (이 프로젝트 전용)

`leanrea` 스킬(`.claude/skills/leanrea/SKILL.md`)은 형식별 분석 명령(First move, Router, Speed patterns)만 담는다. 작업 위치, 탐색 습관, 근거 표기, 도구 유무, Python, 설치는 이 파일에만 있다. 각 규칙은 "관측(실측) -> 원인 -> 조치" 형태로 적는다.

## 의존성은 프로젝트 안에서만
- 프로젝트 메모리는 `.claude/memory/`(Claude Code 메모리 경로 `~/.claude/projects/-home-yh-projects-RE-by-leanrea/memory`가 이곳을 가리키는 심볼릭 링크).
- `.claude/settings.json` env로 Go(`GOPATH`, `GOMODCACHE`, `GOCACHE`)와 npm 캐시를 `.cache/` 아래로 고정하고, `PIP_REQUIRE_VIRTUALENV=true`로 venv 밖 pip 설치를 막는다. `pip install --user`는 쓰지 않는다.

## 작업 위치
- `$D` = `targets/<name>/result/`(중간 결과물, 번호 붙임), `T` = `targets/<name>/` 아래 복사본. 스킬 명령의 `<workdir>`는 `$D`. 스킬 명령의 `python3 -I`는 `.REA/bin/python -I`로 바꿔 실행한다. 일회성 스크립트는 `tmp/<name>/`(분석 완료 후 삭제). 규칙 원문은 루트 `CLAUDE.md`의 디렉토리 절.
- 세션 scratchpad는 위 위치에 맞지 않는 세션 내 임시 확인용으로만 쓴다. 관측: `$TMPDIR`가 비어 있음 -> 원인: 경로 조립 시 `/`로 떨어짐 -> 조치: `$TMPDIR`·`/tmp`로 경로를 만들지 않는다.
- `/mnt/c` 아래 대상: 관측: 9P라 느리고 Windows가 잠글 수 있음 -> 조치: `targets/<name>/`로 복사한 뒤 복사본을 분석한다.

## 탐색 습관
- 관측: `rg`는 숨김·ignore 파일을 건너뜀(Electron `.webpack/`, `.vite/`) -> 조치: 추출 트리는 `rg -uu`.
- 관측: 큰/압축된 파일을 통째로 읽으면 컨텍스트를 소모 -> 조치: `rg -o '.{0,200}NEEDLE.{0,200}' F | head`로 자르고, 디스어셈블은 파일로 한 번 떠서 grep.
- 관측: 독립 조회를 나눠 부르면 왕복이 늘어남 -> 조치: `;`와 `echo '--- name'`으로 한 Bash 호출에 묶고, 출력은 `head`/`-m`으로 제한. zsh는 맨 `==x`를 확장하므로 표지는 따옴표로 감싼다.
- 순서: `file -b`와 매직 바이트로 형식 판별 -> 가장 싼 inventory(imports, strings, exports) -> 그다음에만 디컴파일.
- 관측: `r2`가 매번 "Relocs has not been applied" 경고 -> 조치: `r2 -e bin.relocs.apply=true -qc ...`.

## 근거 표기
- 주장마다 **확인**(file:offset, 심볼, 문자열, 주소 등 실측 근거 인용), **추정**(근거 없는 해석), **미확인**(찾지 못했거나 해석하지 못함) 중 하나로 표시한다. 찾지 못한 사실은 "없음"이 아니라 **미확인**이다. 정적 읽기는 관측된 실행이 아니다.
- **에뮬 관측**: `EMULATION.md` 절차로 얻은 값. 정적 확인보다 낮은 별도 등급이며, 표기에 결과 파일(`result/NN-emu-*`)과 입력 인자를 붙인다. 손으로 따라간 정적 값과 대조되면 확인으로 올린다. 실행 관측 등급은 두지 않는다(1원칙).
- 질문받은 항목마다 근거가 생기면 멈춘다. 목표는 호출 2~4회(일괄 정찰 1회, 표적 조회 1~2회) 후 답변.

## 신뢰 불가 데이터
- 추출·다운로드물은 각자 빈 디렉터리에 풀고, 그 안에서 인터프리터·빌드 도구를 실행하지 않는다. 원인: 인터프리터가 현재/스크립트 디렉터리의 모듈(`json.py` 등)을 먼저 로드한다.

## 도구 (실측: `command -v`, 경로 확인)
- 있음(.REA venv, verified 2026-10-31): `pefile==2024.8.26`, `hermes-dec==0.1.8`, `unicorn==2.1.4`(에뮬레이션 `tools/emu/unicorn_run.py`, 절차는 EMULATION.md). 설치 목록은 `requirements.txt`와 `.REA/bin/pip freeze`가 일치한다.
- 있음: `file rg readelf objdump nm strings ldd jq go r2 binwalk 7z unzip curl node npx python3 gdb strace ltrace llvm-objdump apktool tshark sqlite3 wasm-objdump dotnet upx gcc`, Ghidra `~/tools/ghidra`, `ilspycmd` `~/.dotnet/tools/ilspycmd`, jadx `~/tools/jadx/bin/jadx`(PATH에 없으면 전체 경로).
- 없음: `cargo checksec unblob avr-objdump simavr`. 대체: 같은 형식의 스킬 Router 행 fallback(AVR은 `r2 -a avr`, 펌웨어는 `binwalk`).
- 도구 유무를 근거로 쓰기 전 `command -v`로 다시 확인한다. 원인: 예전 스킬 도구 목록이 8개 도구를 "없음"으로 기술했으나 실측상 모두 설치돼 있었다(목록은 낡는다).

## Python (`.REA` venv)
- 추출물을 읽는 Python은 `.REA/bin/python -I`(시스템 `python3`는 쓰지 않는다. 관측: 2026-10-31 서브에이전트 5개가 `python3 -I`를 씀 -> 원인: 위임 프롬프트에 지시가 없었음(추정) -> 조치: ROUTING.md 위임 규칙에 명시). 신뢰 불가 디렉터리(`targets/<name>/extract` 등)로 `cd`해서 인터프리터를 실행하지 않고 저장소 루트에서 경로 인자로 넘긴다(관측: 2026-10-31 Replace 확인을 extract 안에서 `python3 -`로 실행). 패키지는 사용자가 `requirements.txt`를 보고 `.REA`에 직접 설치한다. 에이전트는 설치하지 않는다.
- 해결(2026-10-31): `.REA/bin/hbc-decompiler`가 "bad interpreter: /home/yh/projects/FindVuln/.venv/bin/python3" -> 원인: venv를 `FindVuln/.venv`에서 옮겨 콘솔 스크립트 shebang, `pyvenv.cfg`의 `command`, `activate*`의 `VIRTUAL_ENV`/프롬프트가 옛 경로를 가리킴 -> 조치: 해당 12개 파일의 경로를 `/home/yh/projects/RE-by-leanrea/.REA`, 프롬프트를 `.REA`로 바꿈. 확인: `.REA/bin/pip --version`, `pip check`(깨진 의존성 없음), `hbc-decompiler --help`, `source .REA/bin/activate`의 `VIRTUAL_ENV`가 `.REA`. 이후 `.REA/bin/pip`, 콘솔 스크립트를 그대로 쓴다.

## 설치
- 요청이 있을 때만, 설치 전 알린다. `sudo`는 비밀번호가 필요하므로 사용자에게 `! sudo apt install ...`로 실행을 요청한다. Python 패키지는 사용자가 `.REA`에 설치하며, 새로 필요한 패키지는 `requirements.txt`에 추가해 알린다. 도구가 없다는 것은 막힘이 아니다: Router 행의 fallback을 먼저 쓴다.
