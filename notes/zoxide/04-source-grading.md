<!-- 목적: zoxide(B-008) 블라인드 분석 노트 01~03을 소스(analysis/zoxide/src, 태그 v0.10.0)와 대조한 채점. 사전 등록(00-anchors.md)의 채점 규칙을 따른다. 근거는 소스 파일:줄과 바이너리 주소. 소스는 이 단계에서 처음 풀었다. -->
# zoxide B-008 소스 채점

소스: `analysis/zoxide/src.tar.gz`(태그 v0.10.0)를 `analysis/zoxide/src`에 풂. 약어: add=`src/cmd/add.rs`, db=`src/db/mod.rs`, cfg=`src/config.rs`, util=`src/util.rs`.

## 단계별 담당 함수 식별 (M-008 앵커 효과)
| 단계 | 식별 | 앵커 | 소스 대응 |
|---|---|---|---|
| S1 데이터 디렉터리 | 0x3e9c0 | 환경 변수 문자열 `lea` | cfg:`data_dir`, db:`open_dir` |
| S2 DB 읽기 | 0x3e9c0 | 오류 문자열 `lea` | db:`deserialize` |
| S3 추가·갱신 | 0x37620 안 0x393af~0x39564 | 오류 문자열 + 호출 순서(읽기-노화-저장) | add:`run`, db:`add_update` |
| S4 노화 | 0x3e820 | 패닉 Location(db/mod.rs:128) + 부동소수점 상수 0.9, 1.0 | db:`age` |
| S5 저장 | 0x40b70 | 패닉 Location(util.rs:157) + 오류 문자열 | db:`save`, util:`write` |
- 5단계 모두 담당 함수 주소를 노트에 적었다("앵커 없음"으로 적은 단계 0개). 이전 사례(ripgrep 3, 7zr 4건이 함수 미식별 누락)와 대비된다.

## 맞음 (12)
| # | 항목 | 소스 |
|---|---|---|
| 1 | `_ZO_DATA_DIR`, `XDG_DATA_HOME`, `.local/share` 참조 | cfg:11-17 (`dirs::data_local_dir`) |
| 2 | 절대 경로 아니면 오류 | cfg:19 |
| 3 | "could not find data directory, please set _ZO_DATA_DIR manually" | cfg:15 |
| 4 | 파일 이름 `db.zo` | db:`open_dir` |
| 5 | 길이 4 미만이면 corrupted data | db:`deserialize` (`bytes.len() < version_size`) |
| 6 | 첫 u32 != 3이면 unsupported version | db:`VERSION=3`, `deserialize` |
| 7 | bincode 직렬화 | db:`serialize`, `deserialize` |
| 8 | 항목 40바이트(경로 24 + rank f64 + last_accessed u64) | db/dir.rs `Dir` |
| 9 | 기존 항목: rank = max(0, rank + 인자), 시각 갱신 | db:`add_update` |
| 10 | 변경 시에만 노화 후 저장 | add:`if db.dirty() { db.age }`, db:`save` (dirty 확인) |
| 11 | 노화: 합계 > 최대값이면 factor = 0.9*max/합계, 끝에서부터 곱하고 1.0 미만 swap-remove | db:`age` |
| 12 | 저장 오류 단계: 생성, 직렬화, 쓰기, 동기화, 이름 변경 | db:`save`, util:`write` |

## 추정 적중 (4)
- 환경 변수 우선순위 `_ZO_DATA_DIR` > XDG > HOME: `dirs::data_local_dir()`.
- 점수 기본 1.0, 시각 초 단위: add:`self.score.unwrap_or(1.0)`, util:`current_time`.
- 제외 글롭·경로 해석·`_ZO_RESOLVE_SYMLINKS`가 S3 앞 단계: add:`run` 루프 앞부분.
- 임시 파일에 쓰고 동기화 후 이름 변경, 임시 이름 무작위: util:`write`, `tmpfile`.

## 누락 (6)
| # | 누락 | 소스 | 관측이 있었나 |
|---|---|---|---|
| 1 | 새 항목의 rank도 `by.max(0.0)`로 0 미만 방지 | db:`add_update` None 분기 | 있음: 0x394eb 근처 저장 값 `[rsp+0x3f8]`. 값 유래를 읽지 않음 |
| 2 | `\n`, `\r` 포함 경로는 건너뜀(`EXCLUDE_CHARS`) | add:`EXCLUDE_CHARS` | 있음: `0x9efb0` 호출 전후 문자 비교. 해석하지 않음 |
| 3 | 제외 글롭에 맞으면 건너뜀, 기본 제외 = 홈 디렉터리(이스케이프된 글롭) | cfg:`exclude_dirs` | 있음: 문자열 "invalid glob in _ZO_EXCLUDE_DIRS" 위치만 확인, 기본값 미해석 |
| 4 | 디렉터리가 아니면 건너뛰는 게 아니라 `bail!("not a directory: ...")`로 종료 | add:`bail!` | 있음: "not a directory: " 참조 0x3a6bf(같은 함수 0x37620). 조건·결과 미해석 |
| 5 | `_ZO_MAXAGE` 기본 10000, `u32` 파싱 | cfg:`maxage` | 있음: 0x52750에서 파싱 오류 문자열. 기본값 미확인으로 둠 |
| 6 | DB 파일이 없으면 데이터 디렉터리만 만들고 파일은 `save`에서 생성 | db:`open_dir` NotFound 분기 | 있음: "unable to create data directory: " 참조 0x4026d. 분기 의미 미해석 |
- 추가로 소스에 있고 노트에 없던 세부: 임시 파일 소유자 복사(`fchown`), 오류 시 임시 파일 삭제, DB 최대 크기 32MiB 제한(고정 폭 정수 인코딩). 위 6개에 합치지 않고 보조로만 기록한다.

## 오답 (0)

## 집계와 판정
- 맞음 12, 추정 적중 4, 누락 6, 오답 0. 사전 등록 판정 기준: 누락 5 이상 -> **M-008 효과 없음(이 사례에서)**.
- 해석(관측 -> 원인): 누락 6건은 모두 S3·S5 주변의 분기·기본값 해석(M-003 유형)이고 담당 함수 미식별 유형(M-008 대상)은 0건이다. 즉 M-008은 "함수를 찾는 문제"는 줄였지만(이전 사례 누락의 약 30% 차지) 지배적 누락 원인인 분기·기본값 미해석은 줄이지 못했다. 추정: M-008에 "찾은 함수의 모든 분기를 해석했는지" 점검이 없기 때문(M-003과 결합 필요).
- 기준선(네이티브 5건 누락 4~6, 오답 0~3) 대비: 누락은 상한과 같고 오답은 0.

## 되먹임
- 누락 2~4(S3 전처리): 이미 얻은 `lea`/문자열 참조에서 해당 분기를 읽으면 잡히는 유형. 이번에는 재분석하지 않음(블라인드 성적 보존).
- 제안(검증 필요): M-003의 체크리스트에 "문자열 참조 지점마다 그 앞의 조건 분기와 반환/계속 여부를 한 줄로 쓴다"를 추가하고 다음 사례에서 누락이 줄어드는지 본다.
