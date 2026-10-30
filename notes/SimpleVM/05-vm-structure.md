<!-- 목적: SimpleVM 분석 노트 단계 05 (VM 구조). 출처: notes/SimpleVM.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## VM 구조
- 레지스터(전역): `0x0804b190` A, `0x0804b194` B, `0x0804b198` C, `0x0804b18c` 임시
- 메모리 200바이트 `0x0804b0a0`, 접근 헬퍼: load `FUN_08048a0b` (A = mem[A]^0x10), store `FUN_08048a2f` (mem[A] = C^0x10)
- 특수 슬롯: mem[0..7] 입력, mem[8] 플래그, mem[9] PC, mem[10] 점프 베이스
- fetch `FUN_08048a48`: A = mem[PC++]
- 디스패처 `FUN_08048c6d`:

| op | 핸들러 | 의미 |
|---|---|---|
| 2 | `FUN_08048b92` | STORE: mem[x] = y |
| 6 | `FUN_08048abb` | XOR: mem[x] ^= mem[y] |
| 7 | `FUN_08048b31` | CMP: mem[8] = (mem[x] == mem[y]) |
| 9 | `FUN_08048bce` | JZ: mem[8]==0이면 PC = mem[10] + x (`FUN_08048a92`) |
| 10 | `FUN_08048c13` | JMP: PC = mem[10] + x |
| 11 | `FUN_08048c22` | HALT: A = mem[0], 반환 1 |
| 그 외 | | 반환 0 (Wrong) |
