<!-- 목적: SimpleVM 분석 노트 단계 03 (안티 언패킹 변조 (seen)). 출처: notes/SimpleVM.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 안티 언패킹 변조 (seen)
1. UPX 매직 `UPX!` 3곳을 `111!`로 변경 (offset 0x78, 0xbdd, 0x13b8). 0xfc7의 `111!`는 압축 데이터이므로 복원하면 안 됨
2. 실제 엔트리 `0xc01bf0`(file 0xbf0)의 4바이트 `e8 52 02 00`을 `90 90 90 90`으로 덮고, 파일 끝(0x13dc) PackHeader 뒤에 복원 스텁 추가: `mov dword [0xc01bf0], 0x000252e8; jmp 0xc01bf0`. e_entry는 이 스텁 `0xc023dc`
3. 첫 PT_LOAD filesz/memsz = 0x13c7 (PackHeader 끝 0x13dc보다 작음)
- 복원 절차 (복사본에서): 매직 복원 -> 0x13dc에서 절단 -> 0xbf0에 `e8520200` -> e_entry=0xc01bf0 -> phdr filesz/memsz=0x13dc -> `upx -d` (2026-10-28 재현: 결과 sha256이 아래 언패킹 해시와 일치. 매직만 복원하면 "header corrupted 1", 엔트리 패치 없이 절단·phdr만 고치면 "mem_size 2")
