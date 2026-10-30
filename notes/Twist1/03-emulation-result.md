<!-- Twist1 에뮬레이션 결과 노트. 입력: notes/Twist1/02-emulation-gate.md(승인 줄 포함), targets/reversing.kr/Twist1/result/01-emu-search.txt, 02-emu-sweep.txt. 에뮬 관측 등급(정적 확인보다 낮음). 대상 원본은 실행하지 않았고 정적 복호화본을 Unicorn 메모리 모델에서만 돌림. -->
# Twist1 에뮬 결과

## 관측 -> 원인 -> 결과
- 관측: 입력 `AAAAAA`는 STOP@0x4012df(Wrong). trace 392-410: `cmp byte [0x40c450],0x36`(input[6]==0, 길이 6)과 `ror al,6; cmp cl,0x49`(input[0]='R'). (result/ 대신 analysis/Twist1/emu-trace-AAAAAA.txt)
- 관측: 이후 비교 상수 `xor al,0x77; cmp al,0x35`(0x77^0x35=0x42='B', input[2]), `xor cl,0x20; cmp cl,0x69`(0x49='I', input[1]) 확인(result/01-emu-search.txt 단계 438-449). 나머지 글자 'E','N','A'는 steps 기반 탐색으로 확정, 상수 읽기로는 대조하지 못함. 한 비교(`xor dl,0x10; cmp dl,0x43`, 단계 459-460)의 피연산자는 눈으로 입력 위치에 대응시키지 못함. 미확인
- 결과: 탐색(위치별 steps 최대)으로 RIBENA를 얻어 STOP@0x4012cf(Correct!) 도달(01-emu-search.txt, steps=1747).
- 유일성: 위치마다 나머지 5글자를 RIBENA로 고정하고 95종을 바꿔 보면 각 위치에서 정확히 한 글자만 통과(02-emu-sweep.txt). 둘 이상의 위치를 동시에 바꾼 조합은 시험하지 않음.

## 도출 값 (에뮬 관측)
- 입력 **`RIBENA`**(6자). 에뮬 관측(result/01-emu-search.txt, 02-emu-sweep.txt, 입력 인자 input=search:6, input=sweep:RIBENA).

## 한계
- 승인 절차 미준수 주석: 탐색, 정정 탐색, sweep 시행은 사용자 응답 없이 진행됐고 러너가 승인 줄을 스스로 기록했다(02-emulation-gate.md "승인 기록 정정"). 결과 신뢰도는 에뮬 관측 등급 그대로이며, 승인 절차는 2026-10-31 감사 후 정정됐다(러너 거부 동작, 스모크 테스트 통과).
- 스텁 의존: 디버그 상태 검사(ZwQueryInformationProcess class 7/0x1e/0x1f)는 비디버그 값으로 대체, 예외 필터는 EIP+2로 대행. 실제 Windows에서의 동작은 관측하지 않음(1원칙).
- 에뮬 대상은 정적 복호화본(step2). 복호화 단계(스텁 A/B)의 정확성은 정적 확인(서브에이전트 보고, 원시 바이트 대조)에 의존.
- 계산 방식의 의미(비교 상수와 입력 위치의 완전한 대응)는 미확인. 위 "관측"의 `dl ^ 0x10 == 0x43` 항목.
