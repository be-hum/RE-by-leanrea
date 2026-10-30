<!-- 목적: zoxide(B-008) 블라인드 분석 단계 01 (대상 식별). 입력: targets/zoxide/zoxide. 생성: curl, tar, sha256sum, readelf, strings, objdump. 이 단계까지 소스 tarball(analysis/zoxide/src.tar.gz)은 풀지 않았다. 범위와 앵커는 00-anchors.md에 사전 등록. -->
# zoxide v0.10.0 (B-008, `zoxide add <path>` 경로)

- 출처: GitHub release v0.10.0 `zoxide-0.10.0-x86_64-unknown-linux-musl.tar.gz`
  - tarball sha256 `2d93385b99f3e82cf2701609a1bffcad863fbeb75aa3fe7eb6be4d29be68b1ae`, 추출 `zoxide` sha256 `0959b169db9adac07187ab99b0d9806f616fbe7938cf84f9f4e2422d8de16e6c`. 릴리스 쪽 체크섬은 확인하지 않음(진위 **미확인**).
- 형식: ELF64 x86-64 static-pie, stripped, Rust(rustc 경로 문자열). 의존: clap_builder 4.6.0, anyhow 1.0.102 등. bincode 계열 문자열("Slice had bytes remaining after deserialization", "Bincode does not support ...").
- 범위와 앵커: `notes/zoxide/00-anchors.md`(S1~S5).
- 읽을거리 정찰에서 환경 변수 8종 문자열: `_ZO_DATA_DIR`, `_ZO_MAXAGE`, `_ZO_EXCLUDE_DIRS`, `_ZO_RESOLVE_SYMLINKS`, `_ZO_ECHO`, `_ZO_FZF_OPTS`, `XDG_DATA_HOME`, `HOME`.
- 도구: `tools/scripts/fn.py`(함수 시작 추정 + 문자열 주석), 패닉 `Location` 재배치 스캔(파이썬 일회성).

## 앵커 적용 기록 (M-008)
1. 패닉 `Location`(경로 문자열을 가리키는 RELATIVE 재배치): zoxide 자체 파일은 `src/db/mod.rs`(줄 128, 148), `src/db/stream.rs`(26, 49, 90, 93, 100), `src/util.rs`(125, 137, 157, 369). 참조 함수: 0x3e820(db/mod.rs:128), 0x42070(db/mod.rs:148), 0x421a0(stream.rs), 0x37620(util.rs:369, 125), 0x51220(util.rs:369), 0x40b70(util.rs:157), 0x51c00(util.rs:137).
2. 오류·환경 변수 문자열 `lea` 참조: 0x3e9c0(데이터 디렉터리, DB 파일 열기·역직렬화), 0x40b70(DB 저장), 0x52750(`_ZO_MAXAGE` 파싱), 0x51220(경로 해석).
3. 공유 상수: 부동소수점 0.9, 1.0 (0xf0fe8, 0xf0fc0) -> 노화 함수 0x3e820.
