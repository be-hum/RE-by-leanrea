<!-- 목적: minisign(B-002) 블라인드 분석 노트 01~03을 소스(analysis/minisign/src, 릴리스 0.12 소스 tarball)와 대조한 채점. 근거는 소스 파일:줄과 바이너리 주소. 소스는 이 단계에서 처음 열었다. -->
# minisign B-002 소스 채점

소스: `analysis/minisign/minisign-0.12.tar.gz`(sha256 `677e3dd52f559992c72be932d958587b5f731a1a295bcee37be878ed3f585926`)를 `analysis/minisign/src`에 풀었다. 구성: `minisign.c`(C), `libzodium.zig`(Zig, libsodium API 모양 구현), `base64.c`, `get_line.c`, `helpers.c`. 약어: m.c=`minisign.c`, z=`libzodium.zig`.

## 맞음 (9)
| # | 항목 | 소스 | 바이너리 |
|---|---|---|---|
| 1 | `.minisig` 기본 경로 = 메시지 경로 + 접미 | m.c:`append_sig_suffix`(~520) | 0x103de07 |
| 2 | 공개키 42바이트(alg 2+keyid 8+pk 32), alg "Ed" 검사 | m.c:237-251 | 0x103ede1 |
| 3 | 1·3행 접두 검사와 길이 제한(103, 8192) | m.c:154-201, `TRUSTEDCOMMENTMAXBYTES` 8192, `B64_MAX_LEN_FROM_BIN_LEN`=((X+2)/3*4+1)+2 | 0x103db9e, 0x103dba4, 0x103dbea |
| 4 | 서명 base64 74바이트, alg "Ed"/"ED" 분기, 그 외 거부 | m.c:211-226 | 0x103dcfb~0x103dd3c |
| 5 | keyid 8바이트 비교와 오류 문자열 | m.c:466-475 | 0x103dfa5 |
| 6 | detached 검증 (sig, msg, len, pk), 실패 시 "Signature verification failed" | m.c:475-480 | 0x103dfcb |
| 7 | 4행 base64 64바이트, 검증 입력 = 서명 64바이트 ‖ trusted comment 본문, 같은 공개키 | m.c:485-496 | 0x103dfe0~0x103e054 |
| 8 | `-H` + 레거시 서명이면 "Legacy (non-prehashed) signature found" | m.c:458-463 (`allow_legacy`) | 0x103df83~0x103e22d |
| 9 | 공개키 기본 경로 `minisign.pub`와 `-p`/`-P` 동시 지정 금지 | m.c:283-293 | 0x103dd4d |

## 추정 적중 (3)
- "ED"=프리해시, "Ed"=레거시: m.c:219-225 `*hashed`.
- 프리해시 = BLAKE2b-512: m.c:76-101(`crypto_generichash_init(...,BYTES_MAX)`), z:45-72(`Blake2b512`). 메시지 길이 64.
- 출력 제어 (`quiet`==0 전체, 2는 trusted comment만, 1은 무출력, `-o` 파일 출력): m.c:513-520.

## 누락 (4)
| # | 누락 | 소스 | 관측이 있었나 |
|---|---|---|---|
| 1 | 공개키 파일 1행(주석)은 읽기만 하고 검사하지 않음 | m.c:255-275 | 있음: 공개키 파일 로더를 읽지 않음(함수 오귀속, 아래 오답 3) |
| 2 | 메시지 로드 방식: 레거시는 `fseeko/ftello`로 전체 길이를 얻어 메모리에 읽고, 프리해시는 64KiB 청크로 스트리밍 해시 | m.c:76-132 | 있음: `0x103ec09`의 `cmp rax,0xffffffffffffffff`(0x103ed09)와 호출 목록. 읽지 않음 |
| 3 | `trim`: `\n`과 `\r`을 모두 제거하고 `\n`이 없으면 0 반환 -> "too long" | helpers.c:159- | 있음: `0x103d3b1` 호출 지점 11곳. 미확인으로 표시 |
| 4 | `-o`이면 정보 출력이 stdout이 아니라 stderr (`info_fp`) | m.c:449-451, 509-518 | 있음: `fprintf` 호출 대상 인자 `[rbp-0x70]` 선택 분기(0x103e09e). 이름만 보고 의미 해석 안 함 |

## 오답 (3)
| # | 내 서술 | 소스 | 원인 |
|---|---|---|---|
| 1 | `0x10360ed` = "libsodium `crypto_sign_ed25519_verify_detached`", 계획 단계의 "libsodium 정적 링크" | 구현은 Zig 표준 라이브러리 `Ed25519.PublicKey.fromBytes` + `sig.verify`, 해시는 `Blake2b512`를 `libzodium.zig`가 libsodium API 모양으로 노출 (z:45-110). 함수 역할(Ed25519 detached 검증)은 맞음, 구현체 서술이 틀림 | API 이름 모양과 "Libsodium" 문자열로 구현체를 단정. M-207 |
| 2 | 단계 3에서 keyid 검사를 단계 4의 메시지 로드보다 앞에 서술 | 순서는 sig_load -> 레거시 검사 -> `message_load` -> keyid 비교 (m.c:457-466). 바이너리 주소는 정확(`call 0x103ec09` 0x103df99가 keyid `cmp` 0x103dfa5보다 앞) | 노트 단계 번호가 주소 순서를 따르지 않음 |
| 3 | `0x103e551/0x103e4e3` = 공개키 파일 파싱 (note 03 미확인 목록의 귀속) | `0x103e551`는 비밀키 로더(`cmp [rbp-0x20],0x9e` = 158바이트 SeckeyStruct, 호출 지점 0x103dd6b는 `-R`), 공개키 파일 로더는 따로 있음 | 호출된 모드 분기와 내부 상수를 확인하지 않고 주변 문자열("minisign.pub")만 본 귀속. M-206 |

범위 밖(채점 제외): Ed25519 내부(소수 order, 정규성 검사)는 Zig std 구현으로 `fromBytes` 실패 시 -1(z:106) 반환까지만 소스 근거가 있고 바이너리 쪽은 읽지 않음.

## 집계
- 맞음 9, 추정 적중 3, 누락 4, 오답 3. 기준선 B-001 (누락 5, 오답 0), B-007 (누락 5, 오답 2).
- 누락은 1 감소(5 -> 4). 오답은 3으로 증가. 오답 원인이 서로 다른 3종(구현체 단정, 순서 서술, 함수 역할 귀속)이라 한 규칙으로 줄지 않는다.
- 추정 -> 확인으로 올라간 M 항목: M-003(3번째 사례).

## 되먹임과 재검증
1. 오답 3: M-206 방법(호출 모드 분기 + 내부 상수)을 `0x103e551`에 적용해 재분석. 호출 지점 0x103dd6b는 `-R` 분기(앞에 "Unsupported signature algorithm" 블록과 `minisign.pub` 기본값 설정 뒤), 내부에 `cmp [rbp-0x20],0x9e`를 확인. 소스와 일치. **잡힘**.
2. 오답 1: M-207 방법(구현 특징 확인)으로 바이너리 쪽을 다시 확인: libsodium 버전 문자열·고유 문자열 검색(`strings`)에서 libsodium 고유 흔적 없음(`sodium_version`·`1.0.xx` 미검출). 접근자 문자열 "ed25519", "blake2b"는 소스 `libzodium.zig`에는 없고 `minisign.c`에도 없는 문자열이라 출처는 아직 미확인(추정: Zig std 내부 상수). 소스와 일치하는 결론은 "libsodium 고유 흔적 없음"까지. **부분적으로 잡힘**; 접근자 문자열의 출처는 미확인으로 남김.
3. 누락 2·4: 재분석 안 함(바이너리 쪽 재읽기 필요). 이번 세션 범위에서는 미수행.
4. 누락 3 (`trim`): 호출 지점의 반환값 사용(`test eax,eax; je` -> "too long" 분기 5곳: 0x103db67, 0x103dbdd, 0x103dc70, ...)은 이미 확인됨. 정확한 `\r` 처리는 미확인으로 남김.
