<!-- 목적: CustomShell 분석 노트 단계 02 (구조). 출처: notes/CustomShell.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 구조
- 가짜 파일시스템 셸: 디렉터리 etc/tmp/bin/var, 파일 passwd/shadow/issue/readme/syslog, 명령 cat/ls(-al)/pwd/whoami/exit.
- 로그인 함수(Ghidra `code:0006ec` 근처 호출부, "Login: "/"Password: "):
  1. Login을 `revkr12`(0x659)와 비교.
  2. Password 8바이트를 `FUN_code_00020c`(바이트 0x418)로 변환, 키 = 0x5be `4a18aff7816ad73a`.
  3. 10바이트 결과를 0x5c6 `9a7d7257d57849e6f202`와 비교.
- 변환 함수 0x418:
  - 1단계 8라운드: 라운드 i마다 키 바이트 k의 비트쌍(&5, &0xa, &0x50, &0xa0)을 표 A(0x624 `0100000203`)로 인덱싱. 이 인덱스로 T[i](0x100+4i, 4바이트)를 XOR하면서 상태 10바이트를 섞음.
  - 2단계 8라운드: 마스크 0x42/0x81/0x24/0x18, 인덱스 함수는 0x3ce(Ghidra `FUN_code_0001e7`).
  - 상태 o[0] = 입력 합 하위, o[9] = 합 상위.
  - 마지막으로 o[1..8]를 `sum % (8-j)`만큼 rotl(0x1180을 udivmod로 가정).
  - 중간 루프는 지연 루프(바쁜 대기)뿐.
