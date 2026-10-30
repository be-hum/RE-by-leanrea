<!-- 목적: xz.exe(B-009) 블라인드 분석 단계 01 (대상 식별). 입력: targets/xz/xz.exe. 생성: curl, unzip, sha256sum, objdump, 파이썬 pefile(오프셋->VA 변환). 소스 tarball(analysis/xz/xz-5.8.4.tar.gz)은 이 단계까지 풀지 않았다. 사전 등록: notes/xz/00-anchors.md. -->
# xz.exe 5.8.4 (B-009, `.xz` 스트림 헤더·푸터 검증)
- 진위: 미확인(릴리스 체크섬·서명 미검증)

- 출처: GitHub release v5.8.4 `xz-5.8.4-windows.zip` (sha256 `f31af7638391ecf286d48bc8555ce6e131691a1c52a9e44303bce57069e9de56`) 안의 `bin_x86-64/xz.exe` (sha256 `855aadc2fe3ebc1ecb3b1e38e99dc517dbd12af948ce515cb3749f1b4d5604cf`). `.sig` 서명은 받지 않았고 검증 도구·공개키도 없어 진위 **미확인**.
- 형식: PE32+ x86-64 console, `file`: "stripped to external PDB", 섹션 `.text`(VA 0x140001000, 0x2f740), `.rdata`(0x140032000), `.data`, `.pdata`, `.rsrc`. imports: KERNEL32와 api-ms-win-crt-* (UCRT) 계열.
- 범위와 앵커: `notes/xz/00-anchors.md`(X1~X5).

## 앵커 적용 기록 (M-008, M-209)
1. 매직 상수: 헤더 매직 `fd 37 7a 58 5a 00`가 `.rdata` 0x1400364d2에, 푸터 매직 `59 5a`("YZ")가 0x1400364d0에 연속 배치(파일 0x346d0, 0x346d2; pefile로 VA 변환). 코드에는 이 주소를 직접 참조하는 `lea`가 없었다(`rg '# 0x1400364d'` 무결과, 코드 바이트 스캔도 동일).
2. 대신 8바이트 포인터 슬롯 `.rdata` 0x14003e240(푸터 매직 포인터)와 0x14003e260(헤더 매직 포인터)가 `mov rax,[rip+...]`로 로드됨(MinGW 자동 임포트 방식으로 추정). 참조 함수: 헤더 쓰기 0x140010cc0, 푸터 쓰기 0x140010d50, 헤더 읽기 0x140014470, 푸터 읽기 0x140014500.
3. 별개의 인라인 비교 `cmp DWORD PTR [rip+...],0x587a37fd`(0x140003bfe, 0x140003c36, 대상 전역 0x140047180)는 xz 도구 자체의 파일 형식 판별(처음 바이트가 xz 매직인지)로 추정.
4. 쓰기/읽기 구분(M-209): 0x140010cc0은 매직 6바이트를 출력 버퍼로 복사(쓰기), 0x140014470은 입력과 비교(읽기).
