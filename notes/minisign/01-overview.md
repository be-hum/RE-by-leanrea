<!-- 목적: minisign(B-002) 블라인드 분석 단계 01 (대상 식별). 입력: targets/minisign/minisign. 생성: curl, tar, sha256sum, readelf, strings. 이 단계까지 소스는 열지 않았다. -->
# minisign (B-002, `-V` 서명 검증 경로)
- 진위: 미확인(릴리스 체크섬·서명 대조 기록 없음, 2026-10-30 점검)

- 출처: GitHub release `0.12` `minisign-0.12-linux.tar.gz` (`targets/minisign/minisign-0.12-linux.tar.gz`)
  - tarball sha256 `9a599b48ba6eb7b1e80f12f36b94ceca7c00b7a5173c95c3efc88d9822957e73`
  - 추출 `minisign-linux/x86_64/minisign` -> `targets/minisign/minisign` sha256 `2c74dffcc1c9a5ee55957c60971998ace2b89f22585631594ec2152c588af8db`
  - 출처 서명(`.minisig`)은 검증하지 않았다. 이 바이너리로 검증할 수 없고(대상 실행 금지) 다른 minisign 구현이 없다. 출처 진위는 **미확인**, 릴리스 별도 체크섬 파일도 없음.
- 형식: ELF64 x86-64 EXEC, 정적 링크, stripped, 심볼·pclntab 없음(`nm`: no symbols). `.comment`에 `clang version 19.1.0 (zig-bootstrap)`, `LLD 19.1.0`.
- 계획의 가정("ELF-C, libsodium 정적 링크")은 추정이었다. 관측: `.comment`가 zig 번들 clang/LLD이고 `Libsodium`, `crypto_*` 접근자 형태 함수가 있음 -> 원인: 미확인(추정: C 소스를 `zig cc`로 빌드한 것이거나 Zig 소스). 소스 언어는 소스를 열기 전에는 **미확인**.
- 범위: `-V` 검증(공개키·`.minisig` 파싱 -> Ed25519 검증 -> trusted comment 검증). 서명 생성, 키 생성, 키 암호화는 범위 밖.
- 소스 tarball은 이 단계에서 받지 않았다(블라인드 단계 종료 후 받음).

## 인벤토리 (result/01, 02)
- `main`은 단일 거대 함수 0x103d41a(스택 0x120c8)에 -G/-R/-C/-S/-V가 모두 인라인. Ghidra `str:` 질의가 "not inside a defined function"을 반환했고 objdump 프롤로그 탐색(`push rbp` + `sub rsp,0x120c8`)으로 시작 주소를 찾음.
- 사용법 문자열: `minisign -V [-H] [-x sig_file] [-p pubkey_file | -P pubkey] [-o] [-q] -m file`.
