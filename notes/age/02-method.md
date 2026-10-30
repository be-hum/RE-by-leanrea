<!-- 목적: age 분석 노트 단계 02 (분석 방법과 도구 이슈). 출처: notes/age.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 분석 방법과 도구 이슈
- Ghidra 12.2: Go 타입 복원(`GoTypeManager.convertIfaceDef`)이 재귀 스택 오버플로로 import 실패. Go 분석기 없이 진행.
- `go tool objdump`: stripped라 "no symbol section"으로 실패.
- 대안: `debug/gosym`으로 pclntab을 읽어 함수 표 생성(`tmp/age/gofuncs`). PIE라 `.gopclntab` 섹션이 없어 `.data.rel.ro`에서 매직 `f1 ff ff ff 00 00`(0x2f6920)으로 탐색.
  - gosym이 돌려준 주소는 실제보다 0x100 작음. 함수 시작의 Go 스택 검사 프롤로그(`cmp r12,[r14+0x10]`)로 +0x100 보정을 확인. 결과는 `targets/age/result/04-gosym-funcs-fixed.tsv`(4197개).
- objdump 디스어셈블에 함수 표로 call 대상을 주석(`tmp/age/ann.py`, 결과 `targets/age/result/05-annotated-encrypt-path.txt`).
- Go 문자열 상수는 `[]byte("...")` 변환이 즉시값 저장으로 펼쳐져 있어 `movabs`/`mov DWORD` 값을 디코딩해 확인.
