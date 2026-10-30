---
name: emulation-tooling-state
description: leanrea 에뮬레이션(Unicorn) 도구 상태와 Twist1에서 얻은 사용 요령
metadata:
  type: project
---

Unicorn 2.1.4가 `.REA`에 설치됨 (verified 2026-10-31). `tools/emu/unicorn_run.py <gate.md> <pe> <profile.py> start= max= stop= input=` 이 구현돼 있고, 프로필 `tools/emu/profiles/twist1.py`가 범위 밖 callee 스텁을 정의한다. 첫 시행 대상은 Twist1(결과 RIBENA, notes/Twist1/03-emulation-result.md).

**Why:** 자기 수정 코드는 정적 선형 디스어셈블이 깨져 에뮬 trace(실행 시점 15바이트를 rasm2로 디스어셈블, `tools/emu/dis_trace.py`)가 가장 싼 해석 수단이었다.

**How to apply:** 새 대상은 프로필만 새로 쓰고, 관문 문서(`notes/<name>/NN-emulation-gate.md`)를 먼저 만든다. 하네스 확인 창이 승인이며 범위(입력, stop, max)가 바뀌면 새 승인이 필요하다. 입력 탐색은 steps 단독 최대 + sweep 유일성 점검 순서.

**승인 흐름(2026-10-31 감사 후):** 요청 글을 보인 턴에는 시행하지 않고 사용자 응답을 기다린다. 승인 줄은 응답 뒤 에이전트가 gate.md에 쓰고, 러너는 같은 범위 줄이 없으면 거부한다. defaultMode=auto라 확인 창을 승인 근거로 쓰지 않는다. 스모크 테스트 통과 기록은 notes/Twist1/02-emulation-gate.md. venv는 `.REA` 경로로 복구돼 `.REA/bin/pip install`을 쓸 수 있다(verified 2026-10-31). 관련: [[flow-first-not-flag]]
