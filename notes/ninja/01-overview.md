<!-- 목적: ninja(B-010) 블라인드 분석 단계 01 (대상 식별과 inventory). 입력: targets/ninja/ninja. 생성: curl(GitHub API로 asset digest 조회), unzip, sha256sum, file, readelf, nm, strings, objdump(-> targets/ninja/result/01-objdump.txt). 이 단계까지 소스(analysis/ninja/src.tar.gz)는 풀지 않았다. -->
# ninja 1.13.2 (B-010, `.ninja_log` 빌드 로그 로드)
- 진위: 확인(`ninja-linux.zip` sha256이 GitHub API asset digest와 일치). 서명 검증은 미수행.
- 출처: GitHub release `v1.13.2`(2025-11-20) `ninja-linux.zip` sha256 `5749cbc4e668273514150a80e387a957f933c6ed3f5f11e03fb30955e2bbead6`, 안의 `ninja` sha256 `607e668f90dd6cd82e1a42ae572647ad1b1fd43063964295b9547836d8c15d99`(290,928바이트).
- 소스(채점용, 미개봉): `analysis/ninja/src.tar.gz` sha256 `974d6b2f4eeefa25625d34da3cb36bdcebe7fbce40f4c16ac0835fd1c0cbae17`(태그 v1.13.2 아카이브).

## 형식
- ELF64 x86-64, EXEC(non-PIE), stripped(`nm`: no symbols), 동적 링크 `libstdc++.so.6`, `libm`, `libgcc_s`, `libc`. C++(std::string, `_Rb_tree`, `__cxa_*` import).
- 섹션: `.text` 0x403fd0, `.rodata` 0x4364a0(파일 오프셋 + 0x400000 = VA).
- 범위 관련 import: `fopen`, `fread`, `fclose`, `memchr`, `sscanf`, `strtol`, `strtoll`, `strtoull`, `unlink`, `__errno_location`, `strerror`, `steady_clock::now`.

## 범위 문자열(파일 오프셋 -> 참조 지점)
| 문자열 | VA | 참조 |
|---|---|---|
| `build log version is too old; starting over` | 0x4372d8 | 0x40fee5 (FUN_0040f3d0) |
| `build log version is too new; starting over` | 0x437308 | 0x40ff15 (FUN_0040f3d0) |
| `# ninja log v%d` (+`\n`) | 0x439460 | 0x40f8d8(sscanf, 로드), 0x410ed4, 0x430a45, 0x431c59, 0x4340c9(쓰기 쪽 후보, 범위 밖) |
| `.ninja_log load` | 0x438144 | 0x40fcd8 (메트릭 이름) |
| `.ninja_log` | 0x438154 | 0x41010c (FUN_00410100), 0x410cde |
| `loading build log %s: %s` | 0x43815f | 0x4102e9 (FUN_00410100), 0x41120e |
| `opening build log: %s` | 0x438190 | 0x410355 (FUN_00410100), 0x411272 |
| `failed recompaction: %s` | 0x438178 | 0x410298 (FUN_00410100), 0x410b25, 0x41114c |

## 도구 관측
- 관측: `tools/scripts/fn.py ... start 0x40fee5`가 TypeError -> 원인: 이 objdump 출력의 직접 call은 `call   403a00 <...>`(0x 접두 없음)인데 `fn.py`는 `call\s+0x...`만 call 대상으로 모음(대상 집합이 비어 함수 시작을 못 찾음) -> 조치: Ghidra `query.sh str:`로 함수 시작을 얻음. `tools/scripts/README.md` 함정에 추가할 것.
