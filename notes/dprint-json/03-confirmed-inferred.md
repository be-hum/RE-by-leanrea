<!-- 목적: dprint-plugin-json 블라인드 분석 단계 03 (확인/추정/미확인). 02-flow.md 항목을 채점 단위로 나눈 표. 소스 대조 전 상태. -->
# 확인 / 추정 / 미확인 (소스 열기 전)

## 확인
1. export 20개, import 0개, 프로토콜 버전 4
2. `get_plugin_info`는 `plugin_info()` 호출 후 `serde_json`으로 직렬화, 결과 JSON을 전역 버퍼(`data[4..6]`)에 저장하고 길이를 반환
3. `get_shared_bytes_ptr()`는 `data[5]`(버퍼 포인터) 반환
4. 값: name `dprint-plugin-json`, version `0.25.2`, config_key `json`, help_url `https://dprint.dev/plugins/json`, update_url `https://plugins.dprint.dev/dprint/dprint-plugin-json/latest.json`
5. JSON 키 이름 camelCase 8종 문자열 존재
6. 의존 크레이트와 버전(jsonc-parser 0.34.0, dprint-core 0.69.1, serde_json 1.0.148), rustc 커밋

## 추정
- config_schema_url = `https://plugins.dprint.dev/dprint/dprint-plugin-json/<버전>/schema.json`
- 호스트가 `memory`를 직접 읽음
- `clear_shared_bytes`는 호스트 입력용 버퍼 할당
- `fileExtensions`/`fileNames`는 `get_plugin_info`가 아닌 파일 매칭 정보에 사용

## 미확인
- 정확한 JSON 출력 문자열과 필드 순서
- 파일 확장자 목록
- 라이선스 텍스트 내용
- 출처 진위
