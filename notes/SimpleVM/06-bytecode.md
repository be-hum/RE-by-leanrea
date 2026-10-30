<!-- 목적: SimpleVM 분석 노트 단계 06 (내장 바이트코드 (정적 디코딩, 대상 미실행)). 출처: notes/SimpleVM.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 내장 바이트코드 (정적 디코딩, 대상 미실행)
- 디코더: `analysis/SimpleVM/re/vm.py` (logical = rol3(raw) ^ 0x20, entry PC = mem[9] = 0x0a)
- `0a: JMP 0x10`, 이후 입력 7바이트 각각에 대해:
  `STORE mem[7]=k; XOR mem[i]^=mem[7]; STORE mem[7]=c; CMP mem[i],mem[7]; JZ fail(0x0c)`
- (k, c): (60,09) (66,02) (15,26) (07,2d) (4c,22) (63,07) (78,10)
- 성공 시 `STORE mem[1]=0; HALT` (A = mem[0] != 0 -> Correct), 실패 `0c: XOR mem[0]^=mem[0]; HALT` (A=0 -> Wrong)
- 따라서 통과 조건은 input[i] = k_i ^ c_i, 즉 `id3*ndh` (7바이트 + 개행, index 8은 0) (inferred: 정적 재구현으로 도출, 실행 검증 안 함)
