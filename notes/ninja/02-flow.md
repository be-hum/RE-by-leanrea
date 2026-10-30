<!-- 목적: ninja(B-010) 블라인드 분석 단계 02 (`.ninja_log` 로드 흐름). 근거: targets/ninja/result/01-objdump.txt(디스어셈블), 02-query-load.txt(query.sh stdout), 03-query-load-full.txt(Ghidra 디컴파일 전문). 입력: query.sh 'str:build log version is too old' 'str:loading build log' 'str:opening build log'. 소스는 아직 열지 않았다. -->
# `.ninja_log` 로드 흐름

## 함수 식별 (사전 등록 단계별, M-008)
| 단계 | 담당 함수 | 근거 |
|---|---|---|
| L1~L5 로드 본체 | FUN_0040f3d0 (이하 Load) | "too old"/"too new" 참조 0x40fee5/0x40ff15, `fopen(...,"r")`, `sscanf("# ninja log v%d\n")` 0x40f8e2 |
| L5 결과 보고·재작성 호출 | FUN_00410100 (이하 Open) | Load 호출 0x410200, "loading build log", "opening build log", "failed recompaction" 참조 |
| 재작성 | FUN_00435a00 (Recompact, 추정 이름) | `.recompact`(0x43c849), `"wb"`, `# ninja log v%d` 참조 |
| 오류/경고 출력 | FUN_00417190 = Error, FUN_00417730 = Warning | 각 함수가 `ninja: error: `(0x43951b), `ninja: warning: `(0x43952a)를 씀 |

## 흐름 (입력 -> 처리 -> 출력)
1. Open: 경로 `.ninja_log`. 빌드 디렉터리 문자열(this+0x128 길이가 0이 아니면)이 있으면 그 디렉터리 + `"/"`(0x43973c) + `.ninja_log`. 확인(FUN_00410100 앞부분).
2. Load 진입: 메트릭이 켜져 있으면(전역 0x646690 != 0) `.ninja_log load` 이름의 시간 측정 객체를 만들고 `steady_clock::now()` 시작, 반환 직전 FUN_00421070으로 종료(이름은 추정: ScopedMetric). 확인(0x40fcd8, 0x40fda4).
3. `fopen(path,"r")` 실패: `errno==2`(ENOENT, `cmp edi,0x2; je 0x40feb0`)면 메시지 없이 반환 2. 그 외 errno는 `err = strerror(errno)` 후 반환 0. 확인(0x40fd80~0x40fda2, 0x40feb0).
4. 줄 읽기: 0x40000(256 KiB) 버퍼, `memchr(...,'\n')`로 줄 끝, 줄이 버퍼 끝에 걸리면 남은 조각을 앞으로 `memmove` 후 `fread`로 채움. 확인(0x40f4fb, Ghidra 디컴파일 `memset(...,0,0x40000)`, `fread(...,0x40000-...)`).
5. 버전 헤더: 버전 변수가 0인 동안(첫 줄) `sscanf(line,"# ninja log v%d\n",&ver)`.
   - `ver <= 6`(`cmp eax,0x6; jle 0x40fee0`) -> err = "too old; starting over", `fclose`, `unlink(path)`, 반환 2.
   - `ver != 7`(`cmp eax,0x7; jne 0x40ff10`) -> err = "too new; starting over", 같은 처리.
   - `ver == 7` -> 같은 줄을 필드 파싱으로 넘김(0x40f900 `test rbp,rbp; jne 0x40f523`). 헤더 줄에는 탭이 없어 다음 6단계에서 건너뛰어진다(추정: 경로상 그렇게 됨, 의도된 처리인지는 미확인).
   - sscanf가 실패하면 ver는 0으로 남아 `<= 6` 경로("too old")로 간다. 확인(분기 구조), 실제 입력으로 관측한 것은 아님.
6. 필드 파싱: 줄을 탭(`memchr(...,9,...)`)으로 나눔. 순서대로 `strtol(,10)` 시작 시각, `strtol(,10)` 종료 시각, `strtoll(,10)` mtime, 그다음 탭까지 출력 경로, 마지막 탭 뒤부터 줄 끝까지 `strtoull(,16)` 명령 해시. 네 번의 탭 탐색 중 하나라도 실패하면 그 줄은 메시지 없이 건너뜀. 확인(0x40f523~, Ghidra `memchr` 4회 중첩).
7. 항목 저장: 출력 경로 문자열로 해시(FUN_004092d0, 시드 0x439440) 후 해시맵(this+0..+0x24, open addressing으로 보임) 조회.
   - 없으면 0x38바이트 항목을 새로 만들어(경로 string, +0x20 해시, +0x28 시작, +0x2c 종료, +0x30 mtime) 삽입하고 고유 항목 수(`[rsp+0x98]`) 증가. 확인(operator new(0x38), FUN_00432240 재해시).
   - 있으면 기존 항목을 재사용해 필드를 덮어씀 -> 같은 경로의 나중 줄이 이김. 확인(LAB_0040f760 경로).
   - 모든 파싱 성공 줄마다 전체 줄 수(`[rsp+0x44]`) 증가. 시작·종료는 32비트로 저장(`strtol` 결과의 하위 4바이트). 확인.
8. EOF(`fread`==0): `fclose`.
   - 한 번도 데이터를 읽지 못함(줄 포인터 null, 빈 파일) -> 반환 1. 확인(0x40f92d -> 0x40fea0).
   - `ver <= 6`이면 재작성 플래그(this+0x58) = 1, 반환 1. 확인(0x40f933). 이 경로의 도달 조건(헤더 판정을 거치지 않고 EOF에 이르는 경우)은 미확인.
   - 전체 줄 수 > 100(`cmp ecx,0x64; jle`)이고 전체 줄 수 > 고유 수 × 3(`lea eax,[rax+rax*2]; cmp ecx,eax; jle`)이면 재작성 플래그 = 1. 반환 1. 확인(0x40f946~0x40f961).
9. Open이 Load 결과를 처리:
   - 반환 0 -> Error("loading build log %s: %s", path, err), Open이 0 반환. 확인(0x4102e9).
   - 반환 0이 아니고 err가 비어 있지 않으면 Warning("%s", err) 후 err 비움 -> "starting over" 메시지는 경고로 출력되고 빌드는 계속. 확인(FUN_00417730 호출).
   - 재작성 전용 모드(인자 param_2 != 0)이면: 반환이 2가 아닐 때만 Recompact 호출, 실패 시 Error("failed recompaction: %s"), 그 결과를 반환. 확인.
   - 일반 모드: 설정 객체(this+0x10)의 +4 바이트가 0일 때(dry run 플래그로 추정)만, 재작성 플래그(this+0x198 = 빌드 로그+0x58)가 켜져 있으면 Recompact, 실패하면 Error("opening build log: %s")로 0 반환. 그다음 경로를 빌드 로그+0x38(this+0x178)에 저장(나중에 쓰기용으로 열 경로, 추정). 반환 1.

## 문자열 참조 지점의 앞 분기와 결과 (M-003 확장)
| 문자열/참조 | 앞 분기 | 결과 |
|---|---|---|
| (메시지 없음) ENOENT, 0x40feb0 | `cmp edi,0x2; je` 0x40fd87 | 건너뜀: 반환 2, 로그 없이 진행 |
| strerror -> err, 0x40fd90 | 위 분기의 불일치 | 오류 종료: 반환 0 -> Open이 "loading build log" Error |
| "too old; starting over" 0x40fee5 | `cmp eax,0x6; jle` 0x40f8ee | 기본값(새로 시작): 파일 삭제, 반환 2, Open에서 경고 |
| "too new; starting over" 0x40ff15 | `cmp eax,0x7; jne` 0x40f8fa | 위와 같음 |
| (메시지 없음) 필드 탭 누락 | `memchr(,9,)` null 검사 4곳 | 건너뜀: 그 줄만 무시 |
| "loading build log %s: %s" 0x4102e9 | Load 반환 == 0 | 오류 종료: Open 0 반환 |
| Warning("%s") | err 길이 != 0 | 계속 |
| "failed recompaction: %s" 0x410298 | 재작성 전용 모드 && Load 반환 != 2 && Recompact 실패 | 오류 출력, Recompact 결과 반환 |
| "opening build log: %s" 0x410355 | dry run 아님 && 재작성 플래그 && Recompact 실패 | 오류 종료: Open 0 반환 |
