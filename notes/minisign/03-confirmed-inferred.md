<!-- 목적: minisign 블라인드 분석 단계 03 (확인/추정/미확인 분류). 02-flow.md 항목을 채점 단위로 나눈 표. 소스 대조 전 상태. -->
# 확인 / 추정 / 미확인 (소스 열기 전)

## 확인
1. `.minisig` 기본 경로 = 메시지 경로 + `.minisig` (0x103de07)
2. 공개키 = base64 42바이트, alg `Ed`(0x6445) 검사 (0x103ede1)
3. .minisig 1행 `untrusted comment: ` 접두, 3행 `trusted comment: ` 접두 검사와 길이 제한(0x67, 0x2000)
4. 서명 base64 = 74바이트(alg 2 + keyid 8 + 서명 64), alg `Ed`/`ED` 분기, 그 외 거부
5. keyid 8바이트 비교
6. 메시지 서명: (sig, msg, len, pk) detached 검증 함수, 실패 시 "Signature verification failed"
7. 4행 base64 = 64바이트, 검증 입력 = 서명 64바이트 || trusted comment 본문, 같은 공개키, 실패 시 "Comment signature verification failed"
8. `-H` 지정 + 레거시 서명이면 "Legacy (non-prehashed) signature found"로 분기 (분기 구조는 확인, 조건 해석은 추정)

## 추정
- `ED` = 프리해시 서명, `Ed` = 레거시 (플래그가 `0x103ec09` 세 번째 인자로 감)
- 프리해시 알고리즘 = BLAKE2b-512 (접근자 "blake2b" + 크기 0x40)
- `0x10360ed` = libsodium `crypto_sign_ed25519_verify_detached`
- `-q`/`-Q`/`-o`가 `[rbp-0x30]`, `[rbp-0x64]` 값으로 출력 제어
- 소스 언어 C(zig cc 빌드) — 소스 열기 전 근거 약함

## 미확인
- `0x103ec09` 내부(파일 읽기 방식, 해시 호출 방식, 큰 파일 처리)
- 공개키 파일 파싱(0x103e551/0x103e4e3): `untrusted comment` 행 처리, 두 번째 행 형식
- trusted comment 줄바꿈 제거 방식(0x103d3b1의 정확한 동작)
- Ed25519 검증 내부(소수 order 검사, S 정규성 검사 등) — 범위상 libsodium 내부
- 출처 서명 검증(릴리스 진위)
- 키 id가 0일 때 등 예외 경로
