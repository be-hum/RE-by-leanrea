<!-- 목적: FlashEncrypt 분석 노트 단계 03 (동작 (에뮬레이션 추적)). 출처: notes/FlashEncrypt.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 동작 (에뮬레이션 추적)
| 프레임(0-base) | 조건 | 연산 | 다음 |
|---|---|---|---|
| 0 | `spw == 1456` | - | 2 |
| 2 | `spwd == 25` | `spw *= spwd` | 3 |
| 3 | `spwd == 44` | `spw = spw + spwd` (add2, spwd는 문자열이라 연결) | 1 |
| 1 | `spwd == 8` | `spw /= spwd` | 5 |
| 5 | `spwd == 88` | `spw *= spwd` | 4 |
| 4 | `spwd == 20546` | `spw %= spwd` | 6 |
- 프레임 6에서 `spw` 표시.
