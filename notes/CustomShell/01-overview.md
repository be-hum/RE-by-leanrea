<!-- 목적: CustomShell 분석 노트 단계 01 (overview). 출처: notes/CustomShell.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
# reversing.kr CustomShell

- CustomShell sha256 `fc7bd4c2c46a503ba90d72c261a7ecf8a6fce7c2e2df34e003ff8affd2d631c9`
- 형식: ELF32 Atmel AVR 8-bit(Arduino 계열 펌웨어), stripped, 정적. .text 0x1806, .data 0x5fa(RAM 0x100~).
- 도구: avr-objdump 없음. Ghidra AVR8(`analysis/CustomShell/CustomShell/decompiled.c`) + `r2 -a avr` 디스어셈블(바이트 주소 = Ghidra 워드 주소 x2).
