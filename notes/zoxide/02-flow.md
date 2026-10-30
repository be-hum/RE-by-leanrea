<!-- 목적: zoxide 블라인드 분석 단계 02 (add 경로 흐름, 단계 S1~S5). 근거는 targets/zoxide/result/fn-*.txt, 01-objdump.txt의 주소. 함수 이름은 별칭. 소스 대조 전 상태. -->
# 흐름: 환경 -> DB 열기 -> 추가/갱신 -> 노화 -> 저장

모든 주소는 `targets/zoxide/zoxide` 가상 주소(PIE, 로드 기준 0).

## S1: 데이터 디렉터리 결정, 함수 0x3e9c0 (result/fn-3e9c0.txt)
- 관측: `_ZO_DATA_DIR`(0xff05a) 조회(0x3e9e3, 호출 0xd6710). 값이 있으면 첫 바이트 `cmp BYTE PTR [r14],0x2f`('/', 0x3ea47)로 절대 경로 검사, 아니면 "_ZO_DATA_DIR must be an absolute path"(0xff0a5 이후).
- 관측: 없으면 `XDG_DATA_HOME`(0x106570, 0x3ea0c) 조회, 절대 경로 검사. 없으면 `.local/share`(0x10657d, 0x3ea8b)를 홈 경로(`HOME`)에 이어 붙임으로 추정. 모두 실패 시 "could not find data directory, please set _ZO_DATA_DIR manually"(0xff066, 0x3ee23).
- 관측: 결과 경로에 `zoxide`(0xff0a5)를 더하고, 파일 이름 `db.zo`(0xf77d3, 0x3eb92)를 더함.
- 관측: 디렉터리 생성 오류 "unable to create data directory: "(0xf42f2, 0x4026d), 읽기 오류 "could not read from database: "(0xf4316, 0x3eed4).
- 추정: 환경 변수 우선순위 `_ZO_DATA_DIR` > `XDG_DATA_HOME` > `HOME/.local/share`, 모두 `zoxide/db.zo`.

## S2: DB 읽기·역직렬화, 함수 0x3e9c0 후반
- 관측: 읽은 바이트열 길이 `cmp r15,0x4; jb 0x406e3`(0x3fa98~0x3faa1) 미만이면 "could not deserialize database: corrupted data"(0xf778a, 0x406e3). 4바이트 이상이면 첫 u32 `mov edx,[rdx]; cmp edx,0x3; jne 0x406f6`(0x3faa7~0x3faac) -> 다르면 "unsupported version (got {}, supports {})"(0xf42c7, 0x4072d).
- 관측: 역직렬화 오류는 "could not deserialize database"(0xf776c, 0x405a0), 바이트가 남으면 "Slice had bytes remaining after deserialization"(bincode 오류 문자열).
- 결과: DB 파일 = bincode 직렬화, 앞 4바이트 버전 u32 == 3, 나머지는 항목 목록.
- 항목 구조(추정): 크기 0x28(40)바이트(`add r15,0x28` 순회, 0x39420): `path`(문자열: cap +0, ptr +8, len +0x10), `rank` f64(+0x18), `last_accessed` u64(+0x20) (0x39444, 0x39469, 0x394eb~0x39512).

## S3: 추가·갱신, add 분기 0x393af~0x39564 (함수 0x37620 안, result/fn-37620.txt)
- 관측: `0x37620`은 하위 명령 전체(add, query, remove 등)를 한 함수에 인라인한 것(`path not found in database`, `no match found`, `fzf` 문자열 참조).
- 관측: 경로마다 항목 벡터를 순회(`cmp QWORD PTR [r15+0x10],rbx` 길이 비교 후 `memcmp`(0x32bcf0), 0x3942a~0x3943a). 일치하면 `rank = max(0, rank + 인자값)`(`addsd xmm0,[rsp+0x3f0]; maxsd xmm0,xmm1(0)`, 0x39444~0x3945b), `last_accessed = [rsp+0x2f8]`(0x39461~0x39469), 변경 플래그 `mov BYTE PTR [rsp+0x198],0x1`(0x39522).
- 관측: 일치하지 않으면 경로 복사(`0x54ef0` 할당 + memcpy 0x32bda0, 0x3947f~0x394a6)해 새 항목을 푸시: rank = `[rsp+0x3f8]`, last_accessed = `[rsp+0x2f8]`(0x394eb~0x39517), 변경 플래그 설정.
- 추정: `[rsp+0x3f0]`, `[rsp+0x3f8]`은 점수 인자(증가량, 기본 1.0 `0xf0fb8`/`0xf0fc0`)이며 시각 `[rsp+0x2f8]`은 현재 시각(초). 경로 앞 단계: 지수 글롭 제외(`_ZO_EXCLUDE_DIRS`, "invalid glob in _ZO_EXCLUDE_DIRS: ", 0xf4444), 경로 해석 `0x51220`("invalid unicode in path: ", "could not resolve path: ", 0xf4389, 0xf43a5, util.rs:369), `_ZO_RESOLVE_SYMLINKS`(0xff01f) 참조(0x38d1a, 0x39207). 이 전처리의 정확한 순서와 조건(디렉터리인지, 제외되면 건너뛰는지)은 **미확인**.

## S4: 노화, 함수 0x3e820 (result/fn-3e820.txt)
- 관측: 인자 xmm0 = 최대값(`_ZO_MAXAGE` 파싱 결과, 0x52750에서 "unable to parse _ZO_MAXAGE as integer: " 오류). 항목 순회로 rank 합계(`addsd`, 간격 0x28, 초기값 -0.0 `0xf0fe0`)를 구해 `ucomisd xmm1,xmm0; jbe 0x3e996`(0x3e8de~0x3e8e2): 합계가 최대값 이하이면 아무 것도 안 함.
- 관측: 초과하면 `factor = 0.9 * 최대값 / 합계`(`mulsd [0xf0fe8]` = 0.9, `divsd xmm1`, 0x3e8e8~0x3e8f0). 모든 항목을 끝에서부터 `rank *= factor`(0x3e939) 후 `ucomisd xmm3,xmm1; jbe`(0x3e943, xmm3 = 1.0 `0xf0fc0`): rank가 1.0 미만이면 마지막 항목을 그 자리로 복사하고 길이 -1(swap-remove, 0x3e949~0x3e97d), 경로 버퍼 해제(0x3e985).
- 결과: 합계가 최대값을 넘으면 모든 rank를 0.9*max/합계 배율로 줄이고 1.0 미만 항목은 삭제. 변경 플래그 설정(`or BYTE PTR [rbx+0x38],al`, 0x3e998).
- 호출: add 분기에서 변경 플래그가 켜졌을 때만 호출(`cmp BYTE PTR [rsp+0x198],0x1; jne 0x39564`, 0x39544~0x3955f).

## S5: 저장, 함수 0x40b70 (result/fn-40b70.txt)
- 관측: 임시 파일 생성 "could not create file: "(0xf4429, 0x414aa), 이름은 영문 대소문자+숫자 문자표 `ABC...xyz0123456789`(0xff6dd, 0x4108b)로 무작위 접미사를 만드는 것으로 추정. 직렬화 "could not serialize database"(0xf77d8, 0x41a1e), 쓰기 "could not write to database"(0xf77b8, 0x41a48), 동기화 "could not sync writes to file: "(0xf43e7, 0x41833), 이름 변경 "could not rename file: {} -> {}"(0xf4409, 0x4198d).
- 결과(추정): 임시 파일에 직렬화한 DB를 쓰고, 동기화한 뒤, DB 파일로 이름 변경. 직렬화 시 맨 앞에 버전 3(u32)을 쓰는 것은 이번에 직접 읽지 않음 -> **미확인**.
- 호출: add 분기 끝에서 노화 직후 호출(0x3956c).

## 미확인
- S3 전처리(제외 글롭, 경로 해석, 디렉터리 확인)의 순서와 조건
- 점수 인자와 시각이 어디서 오는지(기본 증가량 1.0의 출처)
- S5 임시 파일 위치와 권한, 직렬화 형식의 항목 필드 순서
