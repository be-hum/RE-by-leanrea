<!-- 목적: ripgrep(B-003) 채점 후 M-008 재분석. 04-source-grading.md 누락 1~4, 6을 바이너리에서 다시 찾는다. 주의: 소스를 본 뒤의 재분석이므로 방법의 위치 식별력을 시험하는 것이다. 근거: targets/ripgrep/result/05, 06 및 01-objdump 주소. -->
# ripgrep 재분석 (M-008)

## 방법: 패닉 Location의 줄 번호로 함수를 잡는다
- 관측: `crates/ignore/src/gitignore.rs` 경로 문자열(0x3e0d14)을 가리키는 `R_X86_64_RELATIVE` 재배치 7개(`readelf -rW`)가 `.data.rel.ro`의 Rust `Location{ptr,len=30,line,col}`이었다. 줄/열: (268,49), (272,35), (676,14), (488,29), (495,29), (483,25), (683,26) (0x6fdd20, 0x6fdd38, 0x6fdde8, 0x6fdee0, 0x6fdef8, 0x6fdf10, 0x702e98).
- 조치: 배열 인덱싱 패닉 Location(줄 272, 0x6fdd38)을 `lea ... # 0x6fdd38`로 참조하는 코드 2곳(0x944ce, 0x1f0aab)에서 함수 시작 0x93ed0, 0x1f0830을 얻음. 이 함수들이 `globs[i]` 를 인덱싱하는 매칭 함수다.

## 누락 1·2: 매칭 함수 0x93ed0 (result/05)
- 관측: 매치 인덱스 벡터를 끝에서부터 순회: `shl rdx,3` 후 `mov rdi,[rcx+rdx-8]`, `add rdx,-8`(0x94052~0x9407b). -> 마지막 원소부터 보므로 **마지막으로 일치한 규칙이 이긴다**(소스 gi:271 `.rev()`와 일치).
- 관측: 글롭 원소 크기 `idx*5<<4`=80바이트(0x94073~0x94077), 인덱스 범위 검사 `cmp rdi,rsi; jae 0x944ce`(rsi=globs 길이, 패닉 Location 줄 272), 원소의 `+0x49` 바이트가 0이 아니면 건너뜀(`cmp BYTE PTR [rax+rdi+0x49],0; jne 0x94060`, 0x9407f), 통과하면 `+0x48` 바이트를 결과 구분자로 읽음(`movzx r12d,BYTE PTR [rax+0x48]`, 0x94089).
- 해석(추정): `+0x49` = 디렉터리 전용 플래그, `+0x48` = 화이트리스트 플래그. 이 루프는 `is_dir == false` 특수화 복사로 보이며 디렉터리 전용 규칙을 건너뛴다. 디렉터리일 때 복사(루프 조건에 이 검사가 없는 변형)는 이번에 읽지 않음.
- 판정: 누락 1(마지막 일치 우선) **잡힘**, 누락 2(디렉터리 전용 조건) **부분 잡힘**(`is_dir=false` 경로만 확인).
- 보너스: 0x93f00 `cmp WORD PTR [r14],0x2f2e`("./" 접두 검사) -> 경로의 `./` 접두 제거 후 매칭(소스의 `strip` 단계로 추정).

## 누락 3: 규칙 파일 우선순위 (함수 0x1eecb0, result/06)
- 관측: 0x1f0830(매칭 함수)을 호출하는 곳이 한 함수 0x1eecb0 안에 11곳(0x1eed73, 0x1eeefb, 0x1eefb5, 0x1ef021, 0x1ef0b6, 0x1ef3e7, 0x1ef449, 0x1ef514, 0x1ef578, 0x1ef648, 0x1ef69a)이다. 각 호출 뒤 `test rax,rax; je ...`로 결과가 비었는지 보고 다음 매처로 넘어가는 형태이며, 첫 호출의 매처 객체는 `[r13+0x1f0]`(0x1eed37), 마지막은 `[r13+0x210]`(0x1ef69a).
- 판정: "먼저 비지 않은 결과를 채택하는 체인"이라는 구조는 **확인**(소스 dir.rs `matched_ignore`의 `if m_*.is_none()` 체인, 부모 순회 + 절대 부모 순회 = 5종 x 2 근처와 호출 수가 일치). 매처 객체 오프셋과 파일 종류(.rgignore, .ignore, .gitignore, .git/info/exclude, 글로벌) 대응은 **추정/미확인**.

## 누락 4: 글롭 빌더 옵션 (add_line 0x1f5890, result/04)
- 관측: `GlobBuilder::build`로 추정되는 호출(0x1f5e82, 0x1d19f0) 직전에 옵션 바이트 5개를 스택에 구성: `[rsp+0xab]=0`, `[rsp+0xa9]=1`, `[rsp+0xaa]=1`, `[rsp+0xa8]=builder+0x48`, `[rsp+0xac]=builder+0x49`(0x1f5e44~0x1f5e6b). -> 상수 참 2개(`literal_separator`, `backslash_escape`로 추정), 상수 거짓 1개, 빌더 필드 2개(`case_insensitive`, `allow_unclosed_class`로 추정).
- 판정: 옵션의 개수와 값 구조 **확인**, 이름 대응은 **추정**(비트 순서 미확인). **부분 잡힘**.

## 누락 6: `is_absolute`와 `.git` 요구
- 관측: `bpl` 설정(0x1f5ba9, 0x1f5bca)과 검사(0x1f5c1b, 0x1f5c61)는 이미 있었으나 `**/` 접두 건너뛰기까지 추적하지 않았고, `any_git` 로직은 찾지 않았다. 이번에도 **미수행**.

## 보정
- M-008에 구체 단계 추가: (a) 범위 항목마다 고유 앵커(필드 오프셋, 패닉 Location 줄 번호)를 정한다, (b) 앵커로 함수를 잡고 호출 횟수/순서로 역할을 확정한다.
