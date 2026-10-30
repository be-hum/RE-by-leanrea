<!-- 목적: WindowsKernel 분석 노트 단계 02 (구조). 출처: notes/WindowsKernel.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 구조
- exe: WinKer.sys를 서비스로 생성/시작(ADVAPI32 CreateServiceW/StartServiceW). `\\.\RevKr` 열고 DeviceIoControl 0x1000으로 검사 시작, 이후 0x2000으로 결과 조회해 "Correct!"/"Wrong". 문자열 힌트 "Analyze Me,! :> Hint) Keyboard".
- sys `FUN_00011466`(DriverEntry): 장치 `\Device\RevKr` 생성, IRP_MJ_DEVICE_CONTROL = `FUN_00011288`. 모든 CPU에 DPC `FUN_000113e8`로 IDT의 키보드 인터럽트(HalGetInterruptVector(1,..)) 핸들러를 `LAB_0001108c`로 후킹(KiInterruptTemplate 디스패치 주소 교체, OS 버전별 -0x3c/-0x58).
- 후킹 핸들러 -> DPC `FUN_00011266`: `READ_PORT_UCHAR(0x60)` 스캔코드 -> 상태머신 `FUN_000111dc` -> `FUN_00011156`(^0x12) -> `FUN_000110d0`(^0x05).
- 상태(0x13034): 짝수 상태는 아무 바이트(make 코드)나 통과, 홀수 상태는 break 코드(make|0x80) 비교. 불일치 시 실패 플래그 0x1300c=1. 마지막(0xcf) 일치 시 성공 플래그 0x13024=1.
  - 0..7: a5 92 95 b0
  - 100..0x6b: (x^0x12) == b2 85 a3 86
  - 200..0xcf: (x^0x12^5) == b4 8f 8f b2
- ioctl 0x1000: 상태 초기화. 0x2000: 성공 플래그 반환.
