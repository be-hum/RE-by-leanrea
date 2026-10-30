<!-- Twist1 (reversing.kr) 정적 분석 노트(가벼운 경로 서브에이전트 결과 + 직접 확인 요약). 입력: targets/reversing.kr/Twist1/extract/Twist1.exe(sha256 ecd90333e7bd056abce7f5fb9ee406e63238003e049d4aeb1b2465fe72e17dd8). step2 = 정적 복호화(dec1.py, dec2.py)를 적용한 복사본 targets/reversing.kr/Twist1/Twist1.step2.exe. 대상은 실행하지 않음. -->
진위: 미확인 (reversing.kr 배포 zip, 릴리스 체크섬·서명 대조 안 함, sha256만 기록)
# Twist1

## 흐름 (정적)
1. 엔트리 0x407007(.text 끝)에서 0x407013 `xor dword [0x407007],0x23e850`으로 자기 수정, 스텁 A가 0x407077..0x40715e를 XOR 0x34(루프 0x407063)로 복호화. 확인(서브에이전트, 원시 바이트)
2. 스텁 B: .data 0x409000..0x4090bf를 rol 3, .text 0x401000..0x406fff를 ror 3으로 복호화한 뒤 0x40157c로 점프. 확인
3. main 0x401270: 0x401160, 0x401000 호출, SetUnhandledExceptionFilter(0x401140: ctx+0xb8 += 2, -1 반환), "Input: " 출력(0x401205), 입력 읽기(0x401229, `%s`, 버퍼 0x40b970), 검증 0x401240 호출, eax != 0이면 "Correct!", 아니면 "Wrong". 확인
4. 0x401240: 입력을 최대 10바이트 프레임에 복사 후 0x40720d로 점프. 확인
5. 0x40720d 이후: ZwQueryInformationProcess로 DebugPort(7), DebugObjectHandle(0x1e), DebugFlags(0x1f) 검사, 16바이트 복사 후 0x409150 호출, 이후 0x407400~0x407905의 검증 체인이 자기 코드를 덮어쓴다. 구조는 확인, 검증 코어는 미확인.

## 정적으로 시도한 방법 (에뮬 관문 1)
1. 단계별 XOR/ROL/ROR 복호화(dec1.py, dec2.py): 스텁과 .text/.data는 풀렸으나 검증 체인의 실행 중 덮어쓰기는 반영 못 함.
2. 선형 디스어셈블(objdump, r2 pD): 체인이 코드 바이트에 상수 쓰기(mov [코드주소], 즉치)로 자기 코드를 바꿔 어긋남.
3. 상수 쓰기 일괄 적용(patchreplay.py -> Twist1.step3.exe): 쓰기 순서와 작성 코드 자체의 덮어쓰기를 무시해 코드가 깨짐. (관측: 0x407405가 iretd, 0x4074xx가 의미 없는 명령으로 디코딩)
