<!-- 목적: 7zr.exe(B-004) 블라인드 분석 단계 01 (대상 식별). 입력: targets/7zr/7zr.exe. 생성: curl, sha256sum, file, objdump -x/-h, strings. 이 단계까지 소스(7z2605-src.tar.xz)는 받았으나 풀지 않았다. -->
# 7zr.exe (B-004, 7z 시그니처 헤더 검증 경로)
- 진위: 미확인(릴리스 체크섬 미확인, 아래 출처 줄)

- 출처: GitHub `ip7z/7zip` release 26.05 `7zr.exe`
  - sha256 `9bf582b894dfa665f852d7e9112b02290a1c303c2d95a21fcdc41ffcb03143b7`, 602,624바이트. 릴리스 쪽 체크섬 파일은 확인하지 않음(출처 진위 **미확인**).
- 형식: PE32 (i386), console 서브시스템, 섹션 6개: `.text`(VA 0x401000, 0x7aab5), `.rdata`(0x47c000), `.data`(0x48e000), `.rsrc`, `.reloc`. 심볼 없음.
- imports(5 DLL): OLEAUT32, USER32, ADVAPI32, MSVCRT, KERNEL32.
- 범위: 7z 컨테이너의 시그니처 헤더(32바이트) 해석과 검증. 압축 해제, 폴더·코더 파싱은 범위 밖.
- 문자열 정찰: "Unsupported feature", "CRC Error", "Unexpected end of archive", "Headers Error", "Data Error", "There is some data block after the end of the archive" 등(UI/오류 메시지, 함수 연결은 단계 02).

## 함수 식별 방법
- 관측: 7z 시그니처 바이트열 `37 7a bc af 27 1c`가 `.data` 0x48e4e8(파일 0x8cce8)에 있음(파이썬으로 파일 전체 검색). 코드 참조는 `push 0x48e4e8` 한 곳(0x450004).
- 관측: 읽기 쪽은 이 배열을 참조하지 않고 바이트 비교 상수(`cmp BYTE PTR [esi+2],0xbc` 등)로 인라인 -> 조치: `rg 'cmp .*0xbc|0xaf'`로 읽기 함수 후보(0x44dc55, 0x44dcbe)를 찾음. 상수 배열 참조만 찾으면 읽기 경로를 놓친다.
