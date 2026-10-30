<!-- 목적: tools/scripts/의 재사용 스크립트(여러 대상에서 쓴 것) 용도·입력·사용 예와 함정. 생성: 각 스크립트 머리 주석과 사용한 노트(age, restic, minisign, ripgrep, zoxide, xz)를 대조해 작성, 2026-10-30. 대상 1~2개에서만 쓴 스크립트는 tmp/<name>/에 두고 분석 종료 시 삭제한다(루트 CLAUDE.md 디렉토리 절). Python은 `.REA/bin/python -I`로 실행. -->
# tools/scripts

| 스크립트 | 용도 | 입력 -> 출력 | 쓴 대상 |
|---|---|---|---|
| `gosym-funcs/` | stripped Go ELF의 pclntab을 `debug/gosym`으로 읽어 함수 표 복원(M-101) | ELF -> TSV `entry end name` | age, restic |
| `ann.py` | objdump 출력의 call 대상에 함수명을 주석하고 지정 함수 구간만 출력 | 함수 표 TSV + objdump.txt + 함수명들 -> 주석된 디스어셈블 | age, minisign, restic |
| `fn.py` | 함수 표가 없을 때 call 대상 집합으로 함수 시작을 추정하고, 구간을 `.rodata` 문자열 주석과 함께 출력 | ELF/PE + objdump.txt + 문자열 범위 -> 함수 시작 또는 주석된 구간 | ripgrep, zoxide (xz는 tmp-of-edit/05의 B-009 기록) |
| `strann.py` | objdump 구간의 rip 상대 주소·즉시값을 `.rodata` 문자열로 주석 | ELF + objdump.txt + 구간 -> 주석된 구간 | minisign |
| `rust_locs.py` | stripped Rust ELF64의 패닉 `Location`(path, line, col)과 그 참조 명령 주소 표(M-301, M-008 앵커) | ELF + [경로 부분문자열] + [objdump.txt] -> TSV `loc_va path line col [refs]` | ripgrep, zoxide(재작성 후 검증) |

## 사용 예
```sh
# Go 함수 표. PIE는 주소 보정값을 대상마다 실측한다(M-102: age +0x100, restic 0).
(cd tools/scripts/gosym-funcs && go run . "$OLDPWD/targets/<name>/<bin>") > targets/<name>/result/NN-gosym-funcs-raw.tsv

# 함수 표로 call 주석 + 함수 구간 출력
.REA/bin/python -I tools/scripts/ann.py targets/<name>/result/NN-funcs.tsv targets/<name>/result/NN-objdump.txt main.main 'crypto.(*Key).Open'

# 함수 시작 추정 / 구간 덤프
.REA/bin/python -I tools/scripts/fn.py targets/<name>/<bin> targets/<name>/result/NN-objdump.txt <rodata_lo> <rodata_hi> start <addr>
.REA/bin/python -I tools/scripts/fn.py targets/<name>/<bin> targets/<name>/result/NN-objdump.txt <rodata_lo> <rodata_hi> dump <start> [end]

# Rust 패닉 Location
.REA/bin/python -I tools/scripts/rust_locs.py targets/<name>/<bin> src/db/mod.rs targets/<name>/result/NN-objdump.txt
```

## 함정
- `fn.py`: `<rodata_lo> <rodata_hi>`가 문자열 주석 범위(16진수 VA)다. PE에 `0 0`을 주면 주석이 꺼진다(B-009 xz). ELF static-pie는 `readelf -SW`의 `.rodata` 시작~끝, PE는 `objdump -h`의 `.rdata` VMA~VMA+size.
- `strann.py`: `.rodata` 범위가 코드에 상수로 박혀 있다(`RO0,RO1,OFF`, minisign 값). 다른 대상에 쓰기 전에 그 줄을 대상의 `.rodata` VA 범위와 파일 오프셋 차이로 고친다.
- `ann.py`: 함수 표 TSV는 `start end name`(16진수, `#` 주석 줄 무시). `gosym-funcs` 출력과 같은 형식이다. PIE Go면 보정값(M-102)을 적용한 표를 쓴다.
- `gosym-funcs`: go1.20+ pclntab 매직(`f1 ff ff ff 00 00`)만 탐색한다. 그 이전 버전 바이너리는 "pclntab not found"로 끝난다.
- `rust_locs.py`: x86-64 ELF64, `.rela.dyn`의 `R_X86_64_RELATIVE`만 본다. 비-PIE(절대 주소 직접 기록)나 다른 아키텍처는 미지원.
