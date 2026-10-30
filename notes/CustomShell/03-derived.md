<!-- 목적: CustomShell 분석 노트 단계 03 (해). 출처: notes/CustomShell.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 해
- 변환은 바이트 단위 XOR 상수 + 위치 치환이라 역산 가능. 합 후보(0x200~0x2ff)마다 회전을 되돌려 풀이, 합 일치 해 1개.
- Login `revkr12`, Password **`Pw0!mp@3`** (합 616 = 0x268, o[9]=0x02 일치).
- 정적 재구현(`tmp/reversing.kr/CustomShell/cs.py`), 대상 미실행.
