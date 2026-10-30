<!-- 목적: ripgrep 블라인드 분석 단계 02 (gitignore 규칙 흐름). 근거는 targets/ripgrep/result/NN-* 번호, 주소, 문자열 오프셋. 입력: rg 바이너리, 01-objdump.txt, 04-fn-1f5890-addline.txt. -->
# 흐름: 규칙 파일 -> 한 줄 파싱 -> 글롭 -> 매처

주소는 `targets/ripgrep/rg` 가상 주소(PIE, 로드 기준 0). 함수 이름은 내가 붙인 별칭이다.

## 단계 1: 규칙 출처 (문자열 위주, 코드 연결은 일부)
- 관측: `.gitignore`(0x3e8d4b 외), `.ignore`(0x3e9050), `.rgignore`(0x3e90bf), `.git/info/exclude`(0x3e8e29), `.config/git/ignore`(0x3e8d0d), `XDG_CONFIG_HOME`(0x3ea276)가 rodata에 있음. 다수는 매뉴얼 텍스트(`\fB.gitignore\fP` 등 man 형식) 안이라 **문서 문자열이지 코드 사용 증거가 아님**.
- 관측: 코드 사용 증거가 있는 문자열: 정규식 `(?im-u)^\s*excludesfile\s*=\s*"?\s*(\S+?)\s*"?\s*$`(0x42df88 근처) -> 결과: git 설정 파일에서 `excludesfile =` 줄을 정규식으로 읽어 전역 무시 파일 경로를 얻는다(`core.excludesFile` 의미는 추정).
- 관측: "failed to find CWD (global gitignores will be ignored)"(0x3e0f..), "ignoring global gitignore file because CWD is not known"(0x42df..) -> 결과: 전역 무시 파일 처리는 현재 작업 디렉터리를 알아야 하고 실패 시 건너뜀.
- 관측: 패닉 문자열 "Ignore::add_parents called on non-root matcher"(0x42dee2)를 0x10d550이 참조(result/02) -> 결과: 부모 디렉터리의 규칙 파일을 읽어 올리는 `add_parents` 류가 있고 루트 매처에서만 호출 가능.
- 우선순위: 매뉴얼 텍스트에 ".rgignore takes precedence over .gitignore"가 있음(0x3e90..). 코드 순서는 **미확인**.

## 단계 2: 규칙 한 줄 파싱, 함수 0x1f5890 (result/04)
- 관측: 길이 0이면 건너뜀(`test r8,r8; je`), 첫 바이트 `cmp ebp,0x23`('#')이면 상태만 초기화하고 반환(0x1f58a9~0x1f58e6) -> 결과: 빈 줄과 `#` 주석 무시.
- 관측: 끝 두 글자가 `\ `(`cmp WORD PTR [rcx+r8-2],0x205c`, 0x1f58f2)이면 끝 공백 유지 쪽으로 분기, 아니면 끝 공백 제거 쪽 -> 결과(추정): 이스케이프되지 않은 끝 공백은 제거.
- 관측: 앞 두 글자가 `\!`(0x215c) 또는 `\#`(0x235c)이면(0x1f5af9, 0x1f5b03) 부정/주석 해석을 건너뜀. 아니면 첫 글자 `!`(0x21)에서 `[rsp+0x58]=1` 설정하고 1글자 소비(0x1f5ac6, 0x1f5b10) -> 결과: `!`로 시작하면 부정(화이트리스트) 플래그.
- 관측: 첫 글자 `/`(0x2f, 0x1f5aae, 0x1f5b29)에서 플래그 `edx=1`/`bpl` 설정하고 소비 -> 결과(추정): 앞 `/`는 루트 고정(anchored).
- 관측: 끝 글자 `/`(`cmp BYTE PTR [rdi+r15-1],0x2f`, 0x1f5bd3) 후 `[rsp+0x59]=1` 설정, 그 앞이 `\`(`0x5c`, 0x1f5be8)이면 추가로 1글자 더 줄임 -> 결과: 끝 `/`는 디렉터리 전용 플래그이고 제거(앞의 `\`가 있으면 함께 처리).
- 관측: 남은 문자열을 UTF-8 디코딩하며 `/`(0x2f)가 있는지 스캔(0x1f5c83~0x1f5cf9). 없으면 `**/` 리터럴(0x3e0ed2)과 이어 붙이는 포맷 호출(0x1a5cf0, 0x1f5d5c)로 진행 -> 결과(추정): 슬래시가 없는 패턴은 `**/패턴`으로 바뀐다. 있으면 0x1f5d9f로 분기(이어지는 코드 미확인).
- 관측: 길이 2이고 내용이 `**`(`cmp WORD PTR [r14],0x2a2a`, 0x1f5d05)면 길이 2로 분기, 길이 3 이상이고 앞 세 글자가 `**/`(0x1f5d17~0x1f5d2c)면 0x1f5da9로 분기 -> 결과(추정): 이미 `**`로 시작하는 패턴은 접두를 붙이지 않는다.
- 관측: 두 번째 리터럴 `/*`(0x3e0ed7)을 쓰는 포맷 호출(0x1f5dda, 0x1f5df1) -> 어떤 조건에서 `/*`를 붙이는지는 **미확인**.

## 단계 3: 글롭 컴파일과 매처
- 관측: globset 디버그 문자열 "built glob set; N literals, N basenames, N extensions, N prefixes, N suffixes, N required extensions, N regexes"(0x3e004e)와 "glob `...` converted to regex: `...`"(0x3e00xx) -> 결과: 글롭 집합이 여러 전략으로 분류(리터럴, 기본이름, 확장자, 접두, 접미, 필수 확장자, 정규식)되고 나머지는 정규식으로 변환된다.
- 관측: 글롭 오류 문자열: "invalid use of **; must be one path component", "unclosed character class; missing ']'", "invalid character range", "unopened alternate group; missing '{'", "unclosed alternate group; missing '}'", "nested alternate groups are not allowed", "dangling '\\'"(0x42d440~0x42d560) -> 결과: `**`는 경로 구성요소 하나여야 하고 `{a,b}` 중첩 불가, 문자 클래스·이스케이프 오류가 검사됨.
- 관측: 매처 쪽 판정 순서(마지막 규칙이 이기는지), 디렉터리 전용 규칙의 적용 조건, 부정 규칙 처리는 이 세션에서 코드로 읽지 못함 -> **미확인**.
