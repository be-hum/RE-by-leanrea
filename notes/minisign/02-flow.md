<!-- 목적: minisign 블라인드 분석 단계 02 (`-V` 흐름). 근거는 targets/minisign/result/NN-* 번호와 주소. 입력: 01-objdump.txt, 02-main-ann.txt. 생성: tools/scripts/strann.py로 문자열 주석 후 읽음. -->
# 흐름: 공개키 + .minisig + 메시지 -> 검증

주소는 모두 `targets/minisign/minisign`의 가상 주소. 함수 이름은 심볼이 없어 내가 붙인 별칭이다(아래 "별칭 근거").

## 단계 1: 입력 확보 (result/02)
- 관측: `.minisig` 경로 기본값 생성 — 메시지 경로 뒤에 8바이트 상수 `0x676973696e696d2e`를 붙임(0x103de07, 0x103deda). 리틀엔디언으로 `.minisig` -> 결과: `-x`가 없으면 `<file>.minisig`.
- 관측: 공개키 경로 기본값 문자열 `minisign.pub`(0x103dd4d, `-p` 없으면). `-P`로 인라인 키를 주면 파일을 읽지 않고, 둘 다 주면 "A public key cannot be provided both inline and as a file".
- 공개키 디코딩: `cmp [rbp-0x18],0x2a`(42바이트) 후 `cmp WORD PTR [rbx],0x6445`(0x103ede1, 0x103e65f). 0x6445 = "Ed" -> 결과: 공개키 = alg(2) + keyid(8) + Ed25519 공개키(32), base64.

## 단계 2: .minisig 파싱 (result/02, 0x103db50~0x103dd3c)
- 관측: 1행 앞 `untrusted comment: ` 접두 비교(16바이트 `pcmpeqb` 두 번, 0x103db81~0x103db9e) 실패 시 "Untrusted signature comment should start with ...", 길이 제한 실패 시 "Untrusted signature comment too long".
- 관측: 2행 base64 읽기 버퍼 0x67(103)바이트(0x103dba4), 한 줄 확인 `0x103d3b1` 실패 시 "Signature too long".
- 관측: base64 디코더(0x103cebc, `=` 비교 0x3d) 호출에 최대 길이 0x4a(74)와 출력 길이 `cmp [rbp-0x98],0x4a` -> 2 + 8 + 64 = alg + keyid + 서명. 실패 시 "base64 conversion failed - was an actual signature given?".
- 관측: 서명 alg `cmp WORD PTR [r14],0x6445`("Ed") -> 플래그 0, `0x4445`("ED") -> 플래그 1, 그 외 "Unsupported signature algorithm". 결과: "Ed"=레거시(원본 메시지에 서명), "ED"=프리해시. (플래그 의미는 추정: 후속 분기에서 이 값이 `-H`와 OR되고 `0x103ec09`의 세 번째 인자로 감.)
- 관측: 3행 `trusted comment: ` 접두 비교(0x103dc04~0x103dc34), 최대 0x2000 바이트 읽기, 접두 없으면 "Trusted signature comment should start with ...", 없으면 "Trusted comment not present", 길이 초과 "Trusted comment too long".
- 관측: 4행 base64 디코딩 길이 0x40(`edx=0x40`, `cmp [rbp-0x88],0x40`, 0x103df54~0x103df6d) -> 결과: 4행은 64바이트 comment 서명(global signature).

## 단계 3: 정책·keyid 검사 (0x103df83~0x103dfb3)
- 관측: `or [rbp-0x74],ebx; je 0x103e227` — `-H`(rbp-0x74)와 프리해시 플래그를 합쳐 0이면 "Legacy (non-prehashed) signature found"(0x103e22d)로 이동. 결과(추정): `-H` 지정인데 "Ed" 서명이면 거부.
- 관측: `cmp rax,[r14+0x2]`(서명의 keyid 8바이트 vs 공개키 keyid 8바이트, 0x103dfa5~0x103dfad) 불일치 -> "Signature key id in %s is %016lX but the key id in the public key is %016lX"(0x103e254 주변).

## 단계 4: 메시지 로드와 Ed25519 검증 (0x103df99, 0x103dfcb)
- 관측: `0x103ec09(&len, ptr, flag)`(0x103df99): 파일을 읽어 버퍼와 길이를 돌려줌. 프리해시 플래그가 1일 때 해시를 거쳐 길이가 64가 되는지는 이 함수 읽기에서 확인하지 못함(추정).
- 관측: `0x10360ed(sig+0xa, msg, len, pk+0xa)`(0x103dfcb). 인자 순서 서명, 메시지, 길이, 공개키. 반환 0이 아니면 "Signature verification failed"(0x103e25e). 함수 안에 2^51-1(0x7ffffffffffff), -19(0xffffffffffffffed) 상수와 SHA-512 K 테이블 참조(0x10096e0)가 보임.
- 결과: 서명 R||S 64바이트(`sig+0xa`)와 공개키 32바이트(`pk+0xa`)로 Ed25519 detached 검증.

## 단계 5: trusted comment 검증 (0x103dfe0~0x103e05b)
- 관측: 새 버퍼 크기 = 3행 길이 + 0x40(0x103dfef). 앞 0x40바이트에 1행 서명 64바이트를 복사(0x103e007~0x103e02a, `sig+0xa`)한 뒤 `memcpy`(0x103cd8c)로 3행 본문(접두 뒤)을 이어 붙임.
- 관측: `0x10360ed(globalsig(rbp-0xe0), buf, 0x40+len, pk)`(0x103e04e) 실패 시 "Comment signature verification failed"(0x103e270).
- 결과: 4행 서명이 (메시지 서명 64바이트 || trusted comment 본문)에 대한 같은 공개키의 Ed25519 서명이어야 함.

## 단계 6: 출력
- 관측: `[rbp-0x30]`(-q/-Q 상태) 0이면 "Signature and comment signature verified\nTrusted comment: %s\n"(0x103e092) 출력, 2이면 `"%s\n"`(0x103e08b)만 출력(-Q 추정), 1이면 출력 없음(-q 추정). `-o`이면(`cmp [rbp-0x64],0`) 검증 후 메시지를 출력.

## 별칭 근거
- `0x10360ed` = Ed25519 detached 검증: 직전 접근자 `0x10360b4`가 문자열 "ed25519"(0x1000724) 반환, `0x10360a3`가 -65(0xffffffffffffffbf), 직전 함수들이 0x40, 0x20 반환. libsodium `crypto_sign_*` 접근자 모양. 확인: 상수(2^51-1 기수, SHA-512 K). 이름 자체는 추정.
- `0x103cd3e` = "blake2b"(0x100062a) 반환 접근자, 인접 함수가 0x10, 0x40, 0x20 반환 -> `crypto_generichash_*` 접근자 모양(추정). 프리해시 알고리즘이 BLAKE2b인지는 코드로 직접 확인하지 않음.
