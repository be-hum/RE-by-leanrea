# SimpleVM

- sha256 (원본, 패킹): `8b32429a3c7a1ae69a8238618bdc57979bedaec7dd246b4a60e21f56abef3c67`
- sha256 (언패킹): `59539cef3dafd9e43ba479c547d24b0df6a30b7c865aa913434254fdcfbf7e3b`
- 버전: 표기 없음. 출처 reversing.kr challenge n=17 (Zone.Identifier). GCC 4.6.1 (Ubuntu/Linaro 4.6.1-9ubuntu3), BuildID `eb128045...42e6`
- 크기: 5099 bytes (패킹), 9952 bytes (언패킹)

## 형식
- 패킹: ELF32 i386, 섹션 헤더 없음, UPX (4.2.4 `upx -d`로 해제)
- 언패킹: ELF32 i386 동적 링크, stripped. imports `read write pipe fork getuid fflush __stack_chk_fail`

## 안티 언패킹 변조 (seen)
1. UPX 매직 `UPX!` 3곳을 `111!`로 변경 (offset 0x78, 0xbdd, 0x13b8). 0xfc7의 `111!`는 압축 데이터이므로 복원하면 안 됨
2. 실제 엔트리 `0xc01bf0`(file 0xbf0)의 4바이트 `e8 52 02 00`을 `90 90 90 90`으로 덮고, 파일 끝(0x13dc) PackHeader 뒤에 복원 스텁 추가: `mov dword [0xc01bf0], 0x000252e8; jmp 0xc01bf0`. e_entry는 이 스텁 `0xc023dc`
3. 첫 PT_LOAD filesz/memsz = 0x13c7 (PackHeader 끝 0x13dc보다 작음)
- 복원 절차 (복사본에서): 매직 복원 -> 0x13dc에서 절단 -> 0xbf0에 `e8520200` -> e_entry=0xc01bf0 -> phdr filesz/memsz=0x13dc -> `upx -d` (2026-10-28 재현: 결과 sha256이 아래 언패킹 해시와 일치. 매직만 복원하면 "header corrupted 1", 엔트리 패치 없이 절단·phdr만 고치면 "mem_size 2")

## 동작 (언패킹 바이너리 주소)
- `FUN_08048556` (main 역할, `0x08048544`에서 호출)
  - `getuid() != 0`이면 `Access Denied\n` 출력 후 종료. 즉 root로만 동작
  - `Input : ` 출력, `pipe` 2개, `fork`
  - 자식: stdin에서 최대 10바이트 읽고 9번째 바이트(index 8)가 0이 아니면 `Wrong`. 입력 9바이트를 파이프로 보내고, VM 메모리 `0x0804b0a0`(200바이트)를 바이트별 `rol 3`(`FUN_080489aa`)한 뒤 전송
  - 부모: 입력과 메모리를 받아 메모리 `^0x20`, 앞 8바이트를 입력으로 덮고 전체 `^0x10` 저장(평상시 메모리는 `^0x10` 인코딩). `FUN_08048c6d` VM 실행
  - VM 반환 1이고 결과 레지스터(`0x0804b190`) != 0이면 `Correct!\n`, 아니면 `Wrong\n`
  - 출력 문자열은 모두 `str[i] ^ i` (i=1..)로 인코딩: `0x804b060` Access Denied, `0x804b06e` Error, `0x804b074` Wrong, `0x804b07a` Correct! (첫 글자 주소, 2026-10-28 재검증)

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

## 내장 바이트코드 (정적 디코딩, 대상 미실행)
- 디코더: `analysis/SimpleVM/re/vm.py` (logical = rol3(raw) ^ 0x20, entry PC = mem[9] = 0x0a)
- `0a: JMP 0x10`, 이후 입력 7바이트 각각에 대해:
  `STORE mem[7]=k; XOR mem[i]^=mem[7]; STORE mem[7]=c; CMP mem[i],mem[7]; JZ fail(0x0c)`
- (k, c): (60,09) (66,02) (15,26) (07,2d) (4c,22) (63,07) (78,10)
- 성공 시 `STORE mem[1]=0; HALT` (A = mem[0] != 0 -> Correct), 실패 `0c: XOR mem[0]^=mem[0]; HALT` (A=0 -> Wrong)
- 따라서 통과 조건은 input[i] = k_i ^ c_i, 즉 `id3*ndh` (7바이트 + 개행, index 8은 0) (inferred: 정적 재구현으로 도출, 실행 검증 안 함)

## 열린 질문
- 없음. 실행 검증(root 필요)은 하지 않았다
