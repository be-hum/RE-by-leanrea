<!-- 목적: restic 블라인드 분석 단계 01 (대상 식별). 입력: targets/restic/restic. 생성: curl 다운로드 + bunzip2 + sha256sum + go version -m + readelf. 이 단계까지 소스는 열지 않았다. -->
# restic (B-007, 저장소 키 열기 `OpenKey`/`SearchKey` 경로)

- 출처: GitHub release v0.19.1 `restic_0.19.1_linux_amd64.bz2`
  - bz2 sha256 `f415415624dcc452f2a02b8c33641791a8c6d6d3b65bbb3543fcf9a25151585c` (릴리스 `SHA256SUMS`와 일치, 확인)
  - 해제본 `targets/restic/restic` sha256 `20d4142678d0d95ec11a4759def1b73fd9190abc9ca19e4b62d067c0b387e639`
- 형식: ELF64 x86-64, 정적 링크, non-PIE, symtab 제거(`go tool nm`: no symbol section), go1.26.4, 모듈 `github.com/restic/restic`(devel), 의존 모듈 79개 (`go version -m`).
- 범위: 비밀번호로 저장소 key 파일을 열어 마스터 키를 얻는 경로. 백업·복원·청킹·네트워크 백엔드는 범위 밖.
- 소스 tarball `analysis/restic/restic-v0.19.1-src.tar.gz`는 받았으나 풀지도 열지도 않았다(블라인드 단계).

## 함수 표 복원 (M-101, M-102 대조)
- 관측: `.gopclntab` 섹션이 있고 `debug/gosym`이 36,735개 함수를 읽음(`targets/restic/result/01-gosym-funcs-raw.tsv`) -> 원인: 링커가 symtab만 제거, pclntab은 런타임 필요로 유지 -> 조치: M-101 방법 적용(PIE용 `.data.rel.ro` 매직 탐색은 불필요).
- 관측: 함수 entry 0x542660, 0x544c60 모두 `cmp rsp,[r14+0x10]`로 시작(`result/02-objdump.txt`) -> 원인: non-PIE는 gosym 주소와 `.text` 주소가 같음 -> 조치: 보정값 0. age의 +0x100은 PIE 특성이며 M-102를 "대상마다 실측"으로 유지.
