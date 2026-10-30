<!-- 목적: CRC1 분석 노트 단계 02 (구조). 출처: notes/CRC1.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 구조
- `entry` -> `FUN_004011a0`: DialogBoxParamA(리소스 0x65, DlgProc `FUN_004011c0`).
- `FUN_00401000` (DlgProc 초기화 시 호출): CRC-64 테이블 생성(반사형, poly `0xC96C5795D7870F42`, 0x4085e8~0x408de8, 256 x u64). 이어서 0x406030 문자열의 오프셋 0xd0..0xd7을 `e7 51 de 35 a3 13 90 2e`로 덮어씀.
- `FUN_00401070` (버튼 처리): 
  1. GetDlgItemTextA(id 1000, 최대 0x14). 길이가 정확히 8이어야 함.
  2. 0x406030의 256바이트 문자열("_[Hello___Welcome To Reversing.Kr]__The idea ...")을 스택 버퍼에 복사.
  3. 입력 i번째 바이트를 버퍼[i*16]에 삽입(i=0..7).
  4. 256바이트 전체 CRC-64(init 0, final xor 없음).
  5. 결과 == `0x676f5f675f695f6c`("l_i_g_og" LE)이면 id 0x3e9에 "CORRECT", 아니면 "WRONG".
