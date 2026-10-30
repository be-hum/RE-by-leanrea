<!-- 목적: ninja(B-010) 누락·오답 고리를 소스를 본 뒤 바이너리에서 다시 확인한 재분석 기록. 블라인드 성적이 아니며 장부 수치는 바꾸지 않는다(루트 CLAUDE.md 정답 매핑 5). 입력: targets/ninja/result/01-objdump.txt. -->
# B-010 재분석

## 누락 2: 두 번째 Load 호출자
- 방법: query 출력의 `CALLER 00410dab ?`를 objdump에서 직접 읽음.
- 관측: 0x410dab `call 0x40f3d0`, 0x410db2 `je 0x411200`(반환 0 -> 0x41120e "loading build log"), 0x410db8 `cmp eax,0x2; je 0x411096`(NOT_FOUND 별도 처리), 0x410dc1 err 길이 검사 후 0x410dd9 Warning, 0x41118b `.ninja_log restat` 메트릭, 0x41114c "failed recompaction", 0x411272 "opening build log". 소스 ToolRestat(nj:1099-1151)과 일치. **잡힘**.
- 방법 보강: CALLER가 `?`(정의된 함수 밖)이면 M-205처럼 objdump로 호출 지점 주변을 읽는다. M-008 방법에 사례 추가.

## 누락 1: 개행 없는 조각
- 관측: 0x40f900 `test rbp,rbp`(rbp = 줄 끝 포인터) 불일치 시 0x40f909~0x40f919에서 줄 시작·버퍼 끝만 갱신하고 0x40f7f0(다음 읽기)으로 감. 파싱하지 않음. bl:247-249와 일치. **잡힘**.
- 방법 보강: M-003 확장을 "문자열 참조 지점"뿐 아니라 "모든 분기의 양쪽 결과"로 쓰면 잡혔다. 메시지 없는 분기(`continue`, 조기 반환)는 문자열 앵커가 없어 확장 규칙이 닿지 않는다.

## 오답 20: 버전 업그레이드 분기
- 관측: `cmp DWORD PTR [rsp+0xbc],0x6`가 헤더 판정(0x40f8ee)과 EOF(0x40f933) 두 곳에 같은 상수로 나옴. 소스에서는 서로 다른 상수 `kOldestSupportedVersion`(7)과 `kCurrentVersion`(7)이 같은 값이라 컴파일 후 구분되지 않음.
- 교훈: 같은 즉시값이 의미가 다른 두 비교에 쓰이면 "서로 다른 상수가 우연히 같은 값"을 후보로 함께 적는다.
