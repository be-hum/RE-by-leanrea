<!-- 목적: dprint-plugin-json(B-006) 블라인드 분석 단계 01 (대상 식별). 입력: targets/dprint-json/plugin.wasm. 생성: curl, sha256sum, wasm-objdump, wasm-decompile, wasm2wat, strings. 이 단계까지 소스 tarball은 받았으나 풀지 않았다. -->
# dprint-plugin-json plugin.wasm (B-006, export `get_plugin_info`)
- 진위: 미확인(릴리스에 별도 체크섬 없음)

- 출처: GitHub release `0.25.2` `plugin.wasm` (658,096바이트)
  - sha256 `811ca4c6f732bcd6f707bc2f42d42395bb4127cdf829960cf628a18fc149777e`. 릴리스에 별도 체크섬 없음, 진위 **미확인**.
- 형식: WebAssembly MVP v1, 함수 985개, 모듈 이름 `dprint_plugin_json.wasm`, 가져오기(import) 없음(`wasm-objdump -x -j Import`: Section not found), 메모리 1개, 테이블 1개, Custom 섹션 `name`(함수 이름 보존), `producers`, `target_features`.
- 컴파일러: rustc 커밋 `59807616e1fa2540724bfbac14d7976d7e4a3860`(문자열 `/rustc/...`), 크레이트: `jsonc-parser 0.34.0`, `dprint-core 0.69.1`, `serde_json 1.0.148`(경로 문자열).
- 범위: export `get_plugin_info`가 무엇을 어떤 형식으로 돌려주는지(가져오기 없는 모듈의 호스트 인터페이스 포함). 포매팅 본체(`format`)와 설정 해석은 범위 밖.

## 익스포트 (20개, `wasm-objdump -x -j Export`)
`memory`, `check_config_updates`, `clear_shared_bytes`, `dprint_plugin_version_4`, `format`, `format_range`, `get_config_diagnostics`, `get_config_file_matching`, `get_error_text`, `get_formatted_text`, `get_license_text`, `get_plugin_info`, `get_resolved_config`, `get_shared_bytes_ptr`, `register_config`, `release_config`, `set_file_path`, `set_override_config`, 전역 `__data_end`, `__heap_base`.

## 방법
- 관측: `name` 섹션이 있어 함수 이름 복원 불필요(M-101 해당 없음). `wasm-decompile`로 의사 코드, `wasm2wat`로 텍스트를 만들고 export 함수 본문을 읽음.
- 데이터 세그먼트를 직접 파싱(0x100000부터 58,772바이트, 0x10e598부터 124바이트)해 상수 문자열을 복원. `rodata[N]`은 선형 메모리 주소 `1048576 + N`.
