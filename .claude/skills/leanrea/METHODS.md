<!-- 목적: SKILL.md의 Router/Speed patterns가 다루지 못해 실제 분석에서 새로 얻은 방법론 모음. 초기 오답·누락을 어떤 방법으로 바로잡았는지를 관측 -> 원인 -> 방법 -> 사례 형태로 누적한다. -->
# leanrea 방법론 (경험 누적)

## 항목 형식
- `M-NNN 제목` / 적용 조건 / 관측(초기 실패·오답) -> 원인 -> 방법 / 사례(대상, 채점 결과) / 상태
- 상태: 사례 1건이면 **추정**(그 대상에서만 검증), 서로 다른 대상 2건 이상에서 같은 관측과 같은 효과가 나오면 **확인**. 반례가 나오면 적용 조건을 좁히거나 항목을 고친다.
- 새 항목 번호는 마지막 번호 + 1. 기존 항목을 고칠 때는 사례 줄을 추가하고 상태를 다시 판정한다.

## 일반
- M-001 디컴파일 축약·골격만으로 모델링 금지
  - 적용: 디컴파일 출력이 잘렸거나 골격만 보일 때.
  - 관측: 처치 시 XOR만 있다고 모델링해 후보 0개 -> 원인: 잘린 구간(L394 이후)의 rotl 미확인 -> 방법: 잘린 구간은 원시 디스어셈블과 대조해 상태 변경을 모두 열거.
  - 사례: reversing.kr Adventure(초기 오답 -> 정답 문장 도출, 소스 없음). 상태: 추정.
- M-002 선형 풀이는 rank와 해 공간을 먼저 측정
  - 적용: CRC·XOR 등 GF(2) 선형 검사를 역산할 때.
  - 관측: 해 1개 가정, 첫 해가 출력 불가 -> 원인: rank 62로 해 4개 -> 방법: rank 측정, 영공간 전체 열거, 후보 전부 기록 후 선택 기준을 추정으로 표시. 종속변수 조합이 singular면 rank 검사로 조합 선택.
  - 사례: reversing.kr CRC1(rank 62, 해 4), CRC2(조합 singular, 해 30). 상태: 확인(2건).
- M-003 함수의 모든 call 대상과 분기 인자를 해석
  - 적용: 함수 흐름을 기술할 때.
  - 관측: 이름을 아는 호출만 따라가 누락 5건 -> 원인: 간접 호출(전역 함수 변수), bool 인자 분기, 이름만 본 호출(sort.Strings, rand+hex)을 해석하지 않음 -> 방법: call/분기 인자마다 확인/추정/미확인을 붙이고 빈칸을 남기지 않는다.
  - 사례: age v1.2.1 `age -p`(소스 채점: 오답 0, 누락 5). 상태: 추정.

## Go
- M-101 stripped Go 함수 표 복원
  - 적용: stripped Go 바이너리에서 Ghidra import 실패 또는 `go tool objdump`가 "no symbol section".
  - 관측: Ghidra 12.2 `GoTypeManager.convertIfaceDef` 재귀 중단, objdump 실패 -> 원인: Go 인터페이스 타입 복원 재귀, 심볼 테이블 제거 -> 방법: `debug/gosym`으로 pclntab을 직접 읽어 (entry, end, name) 표 생성. PIE는 `.gopclntab` 섹션이 없으니 `.data.rel.ro`에서 매직 탐색(go1.20+ `f1 ff ff ff 00 00`, 다른 버전은 매직이 다름).
  - 사례: age(go1.25, PIE). 상태: 추정.
- M-102 gosym 주소 보정값 실측
  - 관측: gosym 주소 구간이 함수 중간에서 시작 -> 원인: 미확인(추정: textStart 기준 차이) -> 방법: 함수 시작의 스택 검사 프롤로그 `cmp r12,[r14+0x10]`에 맞을 때까지 보정값을 대상마다 측정.
  - 사례: age(+0x100). 상태: 추정.
- M-103 Go 문자열 상수는 즉시값 저장에서 읽기
  - 관측: `lea` 대상이 문자열이 아니라 `[N]byte` 타입 기술자 -> 원인: `[]byte("...")`가 `movabs`·겹친 `mov DWORD` 저장으로 펼쳐짐 -> 방법: 즉시값을 리틀엔디언으로 디코딩하고 겹친 오프셋과 길이 즉시값으로 원문 복원.
  - 사례: age("payload", "header", "age-encryption.org/v1/scrypt", 소스와 일치). 상태: 추정.

## 아키텍처·형식별
- M-201 AVR 데이터 참조: 관측: Ghidra `str:` 참조 없음 -> 원인: 데이터 주소를 `ldi` 쌍으로 조립 -> 방법: 전체 디컴파일 덤프에서 `DAT_mem_` 패턴 검색 + `r2 -a avr -e scr.color=0` 디스어셈블. r2는 바이트 주소, Ghidra는 워드 주소(x2). 사례: reversing.kr CustomShell. 상태: 추정.
- M-202 32/64비트 혼합(heaven's gate): 관측: Ghidra가 검사 함수를 빈 함수로 표시 -> 원인: `push 0x33; call $+5; add [esp],5; retf` 모드 전환 -> 방법: 해당 구간을 objdump `-m i386:x86-64`로 따로 디스어셈블하고 모드 경계(`retf`)마다 해석 모드를 바꾼다. 사례: reversing.kr CRC2. 상태: 추정.
- M-203 import 함수 호출부 찾기: 관측: `query.sh <import명>`이 "no function found" -> 원인: import는 정의된 함수가 아님 -> 방법: 전체 덤프나 CALLER에서 호출부 검색. 사례: reversing.kr WindowsKernel(`READ_PORT_UCHAR`). 상태: 추정.
- M-204 Flash AVM1 숨은 코드: 관측: 버튼 액션이 상태 머신만 돌고 블록 밖(-0x2a)으로 점프 -> 원인: 실제 코드를 앞 비표준 태그(253)에 숨김 -> 방법: SWF 본문 전체를 메모리로 두고 절대 위치로 에뮬레이션, 비상태 연산만 기록. 사례: reversing.kr FlashEncrypt. 상태: 추정.
