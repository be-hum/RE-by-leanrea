<!-- 목적: dprint-plugin-json 블라인드 분석 단계 02 (get_plugin_info 흐름). 근거는 targets/dprint-json/result/01-decompile.dcmp의 함수와 데이터 세그먼트 오프셋. -->
# 흐름: 호스트 -> get_plugin_info -> 공유 버퍼 -> 호스트 읽기

함수 이름은 `name` 섹션의 맹글링된 이름(줄여서 표기).

## 단계 1: 프로토콜 버전
- 관측: `dprint_plugin_version_4()`가 `return 4`(result/01, 파일 앞쪽). -> 결과: 호스트는 이 값으로 플러그인 스키마 버전 4를 판별.

## 단계 2: `get_plugin_info()` (export 290)
- 관측: 스택 96바이트 확보 후 `JsonPluginHandler::plugin_info`(함수 `ZN197_LT_dprint_plugin_json_wasm_plugin_JsonPluginHandler_..._hand_1`, 29298줄)를 호출해 정보 구조체를 `a+8`에 채움.
- 관측: 128바이트 버퍼를 할당(`rust_alloc(128,1)`)하고 `serde_json`으로 `PluginInfo`를 직렬화(`dprint_core::plugins::plugin_info1_102_..._Serialize`, 37572줄)하여 그 버퍼에 JSON을 씀. 실패하면 `unwrap_failed`로 트랩.
- 관측: 완성된 `Vec<u8>`(용량/포인터/길이)을 전역 `data[4..6]`에 저장(`data[4]=cap, data[5]=ptr, data[6]=len`)하고 이전 버퍼는 해제. 반환값은 JSON 길이.
- 결과: 호스트가 반환 길이를 받고 `get_shared_bytes_ptr()`(= `data[5]`)로 포인터를 얻어 선형 메모리에서 JSON 바이트를 읽는 방식(가져오기가 없으므로 호스트가 `memory` export를 직접 읽음).

## 단계 3: 정보 값 구성 (`plugin_info` 함수 29298줄)
- 관측(데이터 세그먼트 디코딩): version = `0.25.2`(6바이트), name = `dprint-plugin-json`(18), config_key = `json`(4바이트, 즉시값 1852797802 = `json`), help_url = `https://dprint.dev/plugins/json`(31), update_url = `https://plugins.dprint.dev/dprint/dprint-plugin-json/latest.json`(64).
- 관측: `format!`(`format_inner`, 템플릿 주소 1054863, 길이 59 = `https://plugins.dprint.dev/dprint/dprint-plugin-json/` 53바이트 + 버전 6바이트 + `/schema.json` 템플릿 조각)로 config_schema_url을 버전이 들어간 문자열로 만듦 -> `https://plugins.dprint.dev/dprint/dprint-plugin-json/0.25.2/schema.json`(추정, 템플릿 끝 조각은 디코딩에서 일부 깨져 보임).
- 관측: 값 6개(name, version, config_key, help_url, config_schema_url, update_url)를 모두 힙 문자열로 복사. 함수 끝의 해제 호출이 문자열 6개(오프셋 a[2], a[5], a[8], a[11], a[14], a[17])와 일치.

## 단계 4: JSON 필드 이름
- 관측: 데이터 0x80297 부근에 `name`, `version`, `configKey`, `helpUrl`, `configSchemaUrl`, `updateUrl`, `fileExtensions`, `fileNames`가 연속 -> 결과: JSON 키는 camelCase. 앞 6개가 위 구조체 필드와 대응.
- 추정: `fileExtensions`와 `fileNames`는 `get_plugin_info`가 아니라 파일 매칭 정보(`get_config_file_matching`)에 쓰임. 이 구조체에는 Vec 필드가 없는 것으로 보이나 이번 세션에서 직렬화 함수의 필드 수를 끝까지 확인하지 않음.

## 단계 5: 버퍼 관리 보조
- 관측: `clear_shared_bytes(n)`는 `n`바이트 0 채움 버퍼를 새로 할당해 `data[4..6]`을 교체하고 새 포인터를 반환(0이면 크기 1의 더미). 호스트가 입력을 넣을 공간을 만드는 용도로 추정(`format`, `set_file_path` 등이 이 버퍼를 읽는다는 것은 미확인).

## 미확인
- `get_plugin_info` 직렬화의 정확한 JSON 문자열(필드 순서, `fileExtensions` 포함 여부)
- `get_config_file_matching`의 확장자 목록, `get_license_text`의 내용 길이(1080바이트로 보임)
