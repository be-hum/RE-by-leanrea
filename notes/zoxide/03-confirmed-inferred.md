<!-- 목적: zoxide 블라인드 분석 단계 03 (확인/추정/미확인 목록). 소스 대조 전 상태. 채점 단위. -->
# 확인 / 추정 / 미확인 (소스 열기 전)

## 확인
1. 환경 변수 `_ZO_DATA_DIR`, `XDG_DATA_HOME`, `.local/share`가 데이터 디렉터리 결정 함수에서 참조됨, 절대 경로 검사 (S1)
2. 절대 경로가 아니면 `_ZO_DATA_DIR must be an absolute path` 오류 (S1)
3. 모두 실패 시 "could not find data directory, please set _ZO_DATA_DIR manually" (S1)
4. 파일 이름 `db.zo` (S1)
5. DB 길이 4 미만 -> corrupted data 오류 (S2)
6. 첫 u32 == 3이 아니면 unsupported version (S2)
7. 직렬화는 bincode 계열 (오류 문자열) (S2)
8. 항목 크기 40바이트, rank f64 +0x18, last_accessed +0x20 (S2/S3)
9. 기존 경로는 길이와 memcmp로 찾아 rank = max(0, rank + 인자), 시각 갱신 (S3)
10. 새 경로는 푸시, rank = 인자, 시각 = 현재 (S3)
11. 변경 시에만 노화 후 저장 (S3/S4)
12. 노화: 합계 > 최대값이면 factor = 0.9 * 최대값 / 합계, 모든 rank에 곱함, 1.0 미만 삭제(swap-remove) (S4)
13. 저장 오류 단계: 생성, 직렬화, 쓰기, 동기화, 이름 변경 (S5)

## 추정
- 환경 변수 우선순위 `_ZO_DATA_DIR` > `XDG_DATA_HOME` > `HOME/.local/share`
- 점수 인자 기본 1.0, 시각 단위 초
- 제외 글롭, 경로 해석, `_ZO_RESOLVE_SYMLINKS`가 S3 앞 단계
- S5 임시 파일 접미사 무작위, 이름 변경 후 DB 교체

## 미확인
- S3 전처리 순서·조건(디렉터리 아님/제외 시 처리)
- 점수 기본값의 출처, 시각 계산
- S5 임시 파일 위치·권한, 버전 쓰기, 항목 필드 직렬화 순서
- `_ZO_MAXAGE` 기본값
