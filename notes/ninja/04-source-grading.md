<!-- 목적: ninja(B-010) 블라인드 노트(03-confirmed-inferred.md)를 소스 v1.13.2와 대조한 채점. 입력: analysis/ninja/src.tar.gz를 analysis/ninja/src에 푼 소스, notes/ninja/00-anchors.md(채점 규칙), 01~03 노트. 줄 번호는 `nl -ba`/`rg -n` 출력에서 옮김. -->
# B-010 채점 (ninja 1.13.2, `.ninja_log` 로드)

소스: `analysis/ninja/src`. 약어: bl=`src/build_log.cc`, blh=`src/build_log.h`, nj=`src/ninja.cc`, ls=`src/load_status.h`, hm=`src/hash_map.h`.

## 맞음 (16)
| # | 항목(03) | 소스 | 바이너리 |
|---|---|---|---|
| 1 | 경로 `.ninja_log`, builddir 있으면 `<builddir>/.ninja_log` | nj:1452-1454 | 0x41010c, 0x43973c |
| 2 | 메트릭 `.ninja_log load` | bl:209 `METRIC_RECORD` | 0x40fcd8 |
| 3 | fopen 실패: ENOENT -> NOT_FOUND, 그 외 strerror -> ERROR | bl:210-216 | 0x40fd87 |
| 4 | 256 KiB 버퍼, `\n` 분리, 경계 줄 memmove + fread | bl:157-206 (`buf_[256 << 10]` bl:200) | 0x40f4fb |
| 5 | 첫 줄 `sscanf(kFileSignature)`, 실패 시 버전 0 -> too old | bl:226-232 | 0x40f8e2 |
| 6 | 버전 < 7: too old, fclose, unlink, NOT_FOUND | bl:230-232, 238-243 | 0x40f8ee, 0x40fee5 |
| 7 | 버전 > 7: too new, 같은 처리. 현재 버전 7 | bl:54-55, 234-236 | 0x40f8fa, 0x40ff15 |
| 8 | 5필드 탭 구분, 시작·종료 10진, mtime `strtoll`, 해시 `strtoull` 16진 | bl:251-303 (시작·종료는 `atoi`, 바이너리에서는 `strtol(,0,10)`로 보임) | 0x40f523~ |
| 9 | 탭 4개 미만 줄은 건너뜀, 헤더 줄도 이 경로로 무시 | bl:254-281 `continue` | 0x40f900 |
| 10 | 경로 키 맵, 같은 경로는 나중 줄이 덮어씀 | bl:288-301 | LAB_0040f760 |
| 11 | 항목 필드: 경로, command_hash u64, 시작·종료 int, mtime | blh:62-65 | 0x38 항목 |
| 12 | 줄 수 > 100 && 줄 수 > 고유 수 × 3 -> 재작성 플래그 | bl:315-321 | 0x40f946~0x40f961 |
| 13 | 빈 파일 -> SUCCESS | bl:308-310 | 0x40fea0 |
| 14 | ERROR -> Error "loading build log", err 있으면 Warning 후 계속 | nj:1458-1466 | 0x4102e9 |
| 15 | 재작성 전용: NOT_FOUND가 아니면 Recompact, 실패 시 "failed recompaction" | nj:1468-1475 | 0x410298 |
| 16 | 재작성 플래그가 있으면 열기 단계에서 재작성, 실패 시 "opening build log" | nj:1478-1483, bl:77-82 | 0x410355 |

## 추정 적중 (4)
| # | 항목(03) | 소스 |
|---|---|---|
| 17 | 반환 0/1/2 = 오류/성공/없음 | ls:18-21 `LOAD_ERROR, LOAD_SUCCESS, LOAD_NOT_FOUND` |
| 18 | 일반 모드 재작성은 dry run이 아닐 때만 | nj:1478 `if (!config_.dry_run)` |
| 19 | 경로 저장은 첫 쓰기 때 여는 지연 열기 | bl:85-86 주석, bl:132-136 `OpenForWriteIfNeeded` |
| 21 | open addressing 맵 + 시드 쓰는 문자열 해시 | hm:43-44 `emhash8::HashMap`, hm:33 `rapidhash` |

## 오답 (1)
| # | 노트 주장 | 소스 | 원인 |
|---|---|---|---|
| 20 | (추정) EOF에서 버전 <= 6이면 재작성 플래그를 세우는 분기는 "헤더 판정 전에 EOF에 이르는 경우"를 위한 것 | bl:312-318 주석 "if we're upgrading versions", `log_version < kCurrentVersion` | 이 분기는 버전 업그레이드용이다. v1.13.2는 `kOldestSupportedVersion == kCurrentVersion == 7`(bl:54-55)이라 사실상 도달하지 않는다. 바이너리에서 두 상수가 모두 7로 접힌 것(`cmp ...,0x6` 두 곳)을 보고도 "같은 상수 두 개"일 가능성을 후보로 적지 않았다(판단 원칙: 후보를 전부 적기 위반). |

## 누락 (2)
| # | 누락 | 소스 | 관측이 있었나 |
|---|---|---|---|
| 1 | 256 KiB 안에 개행이 없는 조각(너무 긴 줄)은 파싱하지 않고 다음 조각으로 넘어감 | bl:247-249 `if (!line_end) continue;` | 있음: 0x40f900 `test rbp,rbp; jne 0x40f523`의 불일치 쪽(0x40f909 -> 0x40f7f0)을 읽지 않고 "헤더 줄이 파싱으로 간다"로만 적음. M-003 확장은 문자열 참조 지점만 대상이라 메시지 없는 분기의 반대쪽 결과가 빠짐 |
| 2 | `-t restat`(ToolRestat)도 Load를 직접 호출: ERROR면 실패, NOT_FOUND면 성공 종료, 경고 출력, Restat 실패 시 "failed recompaction" 재사용, dry run 아니면 OpenForWrite | nj:1099-1151 | 있음: query 출력에 `CALLER 00410dab ?`(함수 미정의)가 있었으나 따라가지 않음. 사전 등록 L5(로드 결과 보고)에 해당 |

## 범위 밖 / 채점 제외
- 03의 미확인 22(탭 5개 이상, 비16진 해시)는 소스에 별도 처리가 없다(마지막 필드를 줄 끝까지 `strtoull`, bl:285-303). 미확인 23(시각 단위)은 Load가 정하지 않음.

## 집계
- 23항목 중 채점 21: 맞음 16, 추정 적중 4, 누락 2, 오답 1(추정 표기 항목).
- 사전 등록 판정 기준(00-anchors.md): 누락 2 -> **유효**. 단, 사례 1건이므로 METHODS 상태 규칙상 M-003 확장은 추정 유지(확인에는 서로 다른 대상 2건 필요).
- 교란 요인: ninja는 공개 코드라 모델 사전 지식이 섞였을 수 있다. 맞음 16건은 모두 바이너리 주소 근거가 있고, 이름·의미만 맞힌 것은 추정 적중으로 따로 셌다.
- 기준선 대비: 네이티브 B-001~B-009 누락 3~6(중앙 5), 오답 0~3. B-010 누락 2, 오답 1.
