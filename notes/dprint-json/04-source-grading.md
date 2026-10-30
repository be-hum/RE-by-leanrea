<!-- 목적: dprint-plugin-json(B-006) 블라인드 분석 노트 01~03을 소스(analysis/dprint-json/src 태그 0.25.2, analysis/dprint-json/core의 dprint-core 0.69.1 crate)와 대조한 채점. 근거는 소스 파일:줄과 WASM 함수. -->
# dprint-plugin-json B-006 소스 채점

소스: 플러그인 `analysis/dprint-json/src.tar.gz`(태그 0.25.2)와, WASM 진입점을 생성하는 의존 크레이트 `dprint-core-0.69.1.crate`(static.crates.io에서 받음, 의존 소스는 대조 보조로만 사용)를 `analysis/dprint-json/src`, `analysis/dprint-json/core`에 풀었다. 약어: wp=`src/wasm_plugin.rs`, mod=`core/src/plugins/wasm/mod.rs`, pi=`core/src/plugins/plugin_info.rs`.

## 맞음 (9)
| # | 항목 | 소스 | WASM |
|---|---|---|---|
| 1 | `get_plugin_info` = `plugin_info()` -> `serde_json::to_string` -> 공유 버퍼 설정, 길이 반환 | mod:294-298, 433-438 | export 290, `serde_json` 직렬화 호출, `data[4..6]` 저장 |
| 2 | `get_shared_bytes_ptr` = 공유 버퍼 포인터 | mod:414-416 | `return data[5]` |
| 3 | `clear_shared_bytes(n)` = 0 채움 n바이트로 교체 후 포인터 반환 | mod:419-421 | export 281 |
| 4 | `dprint_plugin_version_4` = 스키마 버전 상수 4 | mod:409-411 | `return 4` |
| 5 | PluginInfo 6필드, camelCase 직렬화 | pi:5-26 (`rename_all = "camelCase"`) | 필드 이름 문자열, 해제 6개 |
| 6 | name `dprint-plugin-json`, version `0.25.2` | Cargo.toml:2-3, wp:43-44 (`CARGO_PKG_*`) | 18바이트, 6바이트 |
| 7 | config_key `json`, help_url, update_url 값 | wp:46-52 | 즉시값 `json`, 31바이트, 64바이트 |
| 8 | 의존 크레이트 버전 jsonc-parser 0.34.0, dprint-core 0.69.1 | Cargo.toml:28-30 | 경로 문자열 |
| 9 | 직렬화 실패 시 `unwrap`(트랩) | mod:296 | `unwrap_failed` 호출 |

## 추정 적중 (4)
- config_schema_url = `https://plugins.dprint.dev/dprint/dprint-plugin-json/<버전>/schema.json`: wp:48-51.
- `fileExtensions`/`fileNames`는 PluginInfo가 아니라 별도 파일 매칭 정보: pi:31-38 `FileMatchingInfo`, wp:31-32 (`json`, `jsonc`; 빈 file_names).
- 호스트가 import 없이 `memory`와 포인터로 읽음: mod:414-416.
- `clear_shared_bytes`는 호스트 입력용 버퍼: mod:419-429 (`take_from_shared_bytes`).

## 누락 (0)
- 범위(get_plugin_info) 안 누락 없음. 파일 확장자 목록(json, jsonc), 라이선스 텍스트는 범위 밖 미확인으로 두었고 채점 제외.

## 오답 (0)

## 집계
- 맞음 9, 추정 적중 4, 누락 0, 오답 0.
- 해석: `name` 섹션이 보존돼 난이도가 낮다. 이 사례는 WASM 형식의 기준선(name 섹션 있음)이다. name 섹션이 제거된 WASM은 별도 사례가 필요하다.
- 추정 -> 확인으로 올라간 M 항목: M-103(2번째 사례, 겹친 로드 중복 제거).

## 되먹임과 재검증
- 오답·누락 없음. 단, 분석 중 `help_url` 복원에서 `plugiins`처럼 중복 글자가 나온 것을 M-103 규칙(겹친 오프셋과 길이 즉시값)으로 바로잡았다(분석 노트 02 단계 3에는 바로잡은 값만 기록).
