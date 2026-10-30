<!-- 목적: SimpleVM 분석 노트 단계 02 (형식). 출처: notes/SimpleVM.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 형식
- 패킹: ELF32 i386, 섹션 헤더 없음, UPX (4.2.4 `upx -d`로 해제)
- 언패킹: ELF32 i386 동적 링크, stripped. imports `read write pipe fork getuid fflush __stack_chk_fail`
