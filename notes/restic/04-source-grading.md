<!-- 목적: restic(B-007) 블라인드 분석 노트 01~03을 소스(analysis/restic/src, 태그 v0.19.1)와 대조한 채점. 근거는 소스 파일:줄과 바이너리 주소. 소스는 이 단계에서 처음 열었다. -->
# restic B-007 소스 채점

소스: `analysis/restic/restic-v0.19.1-src.tar.gz`를 `analysis/restic/src`에 풀었다(블라인드 분석 노트 01~03 작성 후). 약어: key.go=`internal/repository/key.go`, kdf.go=`internal/crypto/kdf.go`, crypto.go=`internal/crypto/crypto.go`.

## 맞음 (9)
| # | 항목 | 소스 | 바이너리 |
|---|---|---|---|
| 1 | SearchKey -> OpenKey -> LoadKey -> KDF -> Open -> Unmarshal -> Valid | key.go:56-92, 115-181 | 0x8cee00, 0x8ce8c0 (result/03) |
| 2 | salt 64바이트 필수 | kdf.go:12, 48-50 | 0x7e9ed2 |
| 3 | scrypt.Key 출력 64, `Params.Check` | kdf.go:56-70 | 0x7ea00a, 0x7ea086 |
| 4 | 출력 분할 크기·오프셋 | kdf.go:76-79 | 0x7ea0b6~0x7ea0ed |
| 5 | Open: Valid 선검사, poly1305Verify 후 AES-256 CTR | crypto.go:286-322 | 0x7e9992, 0x7e9aa0, 0x7e9b4d, 0x7e9bab |
| 6 | 힌트 경로(Find -> OpenKey)와 목록 순회 경로, 로그 문자열 6종 | key.go:118-170 | 0x8cee00~, 0x8cf540 |
| 7 | LoadKey = LoadRaw + Unmarshal | key.go:183-197 | 0x8cfa60 |
| 8 | key 파일 JSON 필드 | key.go:30-40 | json 태그 `strings` |
| 9 | 마스터 키 JSON `mac`/`encrypt` | crypto.go:36-39 | json 태그 `strings` |

## 추정 적중 (3)
- 출력 분할의 의미 `[32:64]`=MAC(K,R), `[0:32]`=AES 키: kdf.go:73-79 (note 02 단계 3, 추정이었음).
- Poly1305-AES(nonce를 AES-128로 암호화해 s 생성), 태그는 암호문 끝 16B: crypto.go:66-77, 305-306 (note 02 단계 4).
- 성공 시 cancel로 순회 중단: key.go:158 `cancel()` (note 02 단계 1).

## 누락 (5)
| # | 누락 | 소스 | 관측이 있었나 | 조치 |
|---|---|---|---|---|
| 1 | `k.KDF != "scrypt"` 확인 | key.go:67-69 | 있음: `cmp QWORD PTR [rax+0x40],0x6` 0x8ce972 | 내가 건 `rg -v`에 `memequal`을 넣어 비교 호출을 숨김. M-005 |
| 2 | 비밀번호 틀림(ErrUnauthenticated)이면 다음 key로 계속 | key.go:149-153 | 있음: `errors.Is` 0x8cf9d8 | 인자가 전역 변수(0x2183680)라 대상 미해석. M-003 |
| 3 | maxKeys 제한 (`checked > maxKeys` -> ErrMaxKeysReached) | key.go:139-141 | 있음: `test rsi,rsi; jle` + `cmp rsi,r8; jge` 0x8cf5c5 | 클로저 첫 구간을 읽지 않음. M-003 |
| 4 | `Valid()` = user 키 && master 키 | key.go:310-312 | 있음: `crypto.(*Key).Valid` 두 번 0x8d071a, 0x8d0734 | 두 호출 수신자를 구분하지 않음. M-003 |
| 5 | MAC이 암호문(ct)만 덮고 nonce는 AES로 s에 들어감 | crypto.go:305-312, 66-77 | 있음: `sub r10,rbx` 0x7e9a88 | "미확인"으로 둠. 표기는 정직했음 |

## 오답 (2)
| # | 내 서술 | 소스 | 원인 |
|---|---|---|---|
| 1 | "nonce 길이 != 16이면 'nonce is invalid'" | 길이 != 16은 `panic("incorrect nonce length")`(crypto.go:292-294, 0x7e9c85 -> gopanic). "nonce is invalid"는 nonce가 전부 0일 때(crypto.go:296-298, `validNonce` crypto.go:`sum>0`, 바이너리는 16바이트 OR 루프 0x7e99e9~0x7e9a02) | 가까운 `cmp rsi,0x10`을 문자열에 귀속. M-004 |
| 2 | "암호문 길이 16 이하면 'ciphertext too short'" (`cmp rax,0x10; jbe` 0x7e99f4~0x7e9a02) | `len(ciphertext) < Overhead()`(16)일 때(crypto.go:300-303, 바이너리 `cmp rbx,0x10; jge` 0x7e9a10) | 위 루프를 길이 검사로 오독. M-004 |

범위 밖(채점 제외): Init/AddKey 기본 N, r, p는 note 03에서 미확인으로 남겼고 값은 의존 모듈 `simple-scrypt` 기본값이라 이 소스 트리에 없다.

## 집계
- 맞음 9, 추정 적중 3, 누락 5, 오답 2. 기준선 B-001(age): 맞음 9, 추정 적중 2, 누락 5, 오답 0.
- 지표: 누락 5(기준과 같음), 오답 2(기준 0보다 나쁨). 추정 -> 확인으로 올라간 M 항목: M-003, M-101, M-102 (3건).

## 되먹임과 재검증
1. 누락 1 (KDF 문자열 비교): 이미 있던 result/03에서 `rg -n 'cmp +.*,0x6' ` 한 번으로 `0x8ce972`가 보임 -> M-005로 필터 규칙 정정. 재검증: 같은 파일에서 `memequal`을 빼고 다시 걸러 해당 행을 확인함(OpenKey 37번째 행). 잡힘.
2. 누락 3 (maxKeys): result/06 0x8cf5c5~0x8cf5ca의 `test/jle`, `cmp/jge`와 함수 인자(rsi=maxKeys, r8=checked 증가분)로 읽을 수 있고 바로 소스와 일치(key.go:139). 잡힘.
3. 오답 1·2: 새 방법 M-004(문자열 블록으로 점프하는 `jcc`를 역추적)로 0x7e9a00 `test cl,cl; jbe 0x7e9bf7`(문자열 블록 "nonce is invalid"로 점프)와 0x7e9a10 `cmp rbx,0x10; jge 0x7e9a4c`(통과 시 건너뜀)를 다시 읽어 소스와 일치 확인. 잡힘.
4. 누락 2 (errors.Is의 전역 변수): crypto.init(result/07)은 `fmt.errorf`로 오류를 만들지만 대입 주소를 정적으로 특정하지 못했다. 3회 시도 미만이지만 이번 세션에서는 미확인으로 둔다. M-003의 "간접 호출·전역 변수" 항목은 이 고리에서 아직 확인되지 않음.
5. 누락 4 (Valid 수신자): 호출 직전 rax에 로드되는 필드 오프셋을 읽으면 구분 가능하나 이번에는 수행하지 않음.
