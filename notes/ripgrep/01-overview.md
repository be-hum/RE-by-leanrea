<!-- 목적: ripgrep(B-003) 블라인드 분석 단계 01 (대상 식별과 인벤토리). 입력: targets/ripgrep/rg. 생성: curl, sha256sum, readelf, strings. 이 단계까지 소스는 열지 않았다(소스 tarball은 받았으나 풀지 않음). -->
# ripgrep (B-003, `.gitignore` 규칙 매칭 경로)
- 진위: 확인(릴리스 `.sha256`과 일치, 아래 출처 줄). 같은 릴리스 채널의 체크섬이라 서명 검증은 미수행

- 출처: GitHub release `15.2.0` `ripgrep-15.2.0-x86_64-unknown-linux-musl.tar.gz`
  - tarball sha256 `33e15bcf1624b25cdd2a55813a47a2f95dbe126268203e76aa6a585d1e7b149c` (릴리스 `.sha256`과 일치, 확인)
  - 추출 `rg` sha256 `e62198eb19b136b88c330af83647b5a962cb99b6b1f066758568f12de1974849`
- 형식: ELF64 x86-64 static-pie, stripped(symtab 없음), `.comment`에 `GCC 9.4.0`과 `rustc 1.99.0-nightly (da80ed070 2026-07-14)`. rustc 커밋 `da80ed0708a09dc096c184345d6eb42cbcd50a1e`.
- 크레이트(경로 문자열): aho-corasick 1.1.4, bstr 1.13.0, memchr 2.8.3, regex-automata 0.4.15, regex-syntax 0.8.11, walkdir 2.5.0, same-file 1.0.6, encoding_rs 0.8.35 등. 워크스페이스 크레이트 경로 `crates/ignore/src/{gitignore,dir,walk,types}.rs`, `crates/globset/src/{lib,glob,pathutil}.rs`가 패닉 위치 문자열로 존재(확인).
- 범위: `.gitignore` 규칙 한 줄의 해석과 매칭 경로. 파일 내용 검색, 출력, 타입(-t) 필터는 범위 밖.

## 함수 식별 방법 (M-205 적용)
- 관측: 심볼·pclntab 없음, Rust 문자열은 NUL 종료가 아니라 연속 배치 -> 원인: Rust `&str` 리터럴은 (ptr,len)이라 문자열 풀에 이어 붙음 -> 조치: 패닉 위치용 경로 문자열과 로그 문자열의 주소를 찾고 objdump에서 `# 0x주소` 참조(rip 상대 lea)를 검색, call 대상 집합으로 함수 시작을 추정(`tools/scripts/fn.py`).
- 관측: `crates/ignore/src/gitignore.rs` 문자열(0x3e0d14)을 참조하는 `lea`가 0x10dc1b, 0x1f253a 두 곳 -> 함수 시작 추정 0x10d550, 0x1f23a0 (result/02, 03).
