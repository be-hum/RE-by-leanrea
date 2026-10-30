<!-- Music-Player (reversing.kr) 정적 분석 노트. 입력: targets/reversing.kr/Music-Player/extract/Music_Player.exe (sha256 a71f2e3e118342b8a14b6ce499e426e4f10adf972b03afdd97af86958d35ba93, VB6 네이티브). 근거: objdump -d(전체 디스어셈블), Ghidra 질의 FUN_00404800/FUN_004044c0, BSTR/double 상수 디코딩. 대상은 실행하지 않음. 임시 산출물: tmp/reversing.kr/musicplayer/. -->
진위: 미확인 (reversing.kr 배포 zip, 릴리스 체크섬·서명 대조 안 함, sha256만 기록)
# Music-Player

## 흐름
1. 재생: FUN_004038d0이 ClsMCI로 MPEGVideo를 열고 타이머를 600ms로 설정. 확인(서브에이전트 Ghidra 질의)
2. 타이머 핸들러 FUN_004044c0(thunk 0x4023c5): MCI 위치 pos를 읽는다(0x404545 `[edx+0x44]`). 확인
   - 검사 A: `cmp eax,0xea60; jl`(0x404563). pos >= 60000이면 Form+0x708 호출, MsgBox(아이콘 0x40) 후 종료(0x4045f9). 확인
   - pos < 60000이면 pos/100.0(double 0x4011d0 = 100.0)을 `__vbaFpI4`로 정수화(0x40464c). 600 초과(0x40465a)이면 폼 필드 +0x38 = BSTR 0x402bd0 = "LI". 확인
     - 정수화는 반올림이라 정상 경로(pos < 60000)에서는 도달 불가(pos/100 < 600). 검사 A를 우회해 이 분기에 들어오면 pos가 약 60050 이상일 때만 세트됨. 추정(반올림 모드 가정)
   - 검사 B: 위치를 다시 읽어 `cmp [ebp-0xa4],0xea6a`(0x404704, 60010). 초과이면 필드 +0x40 = Chr(0x72) 와 "a"(0x402bdc), "e"(0x402be4)의 연결 = "are". 확인(연결 순서는 아래)
3. 폼 이벤트 FUN_004040c0(thunk 0x402391): 필드 +0x3c = StrCat(BSTR 0x402b98 "te", BSTR 0x402ba4 "n") = "ten". 확인. 이 핸들러가 어떤 이벤트인지는 객체 테이블을 해독하지 않아 미확인.
4. 플래그 조립 FUN_00404800(thunk 0x4023d2): 시간 라벨(vtable +0x50)의 Mid(text,1,2)을 숫자로 바꿔 0.0(double 0x11e8)보다 크면 폼 속성(vtable +0x54, 캡션으로 추정)을 `__vbaVarCat` 15단 체인으로 설정. 확인(디컴파일)

## 연결 순서 (관측 -> 원인 -> 결과)
- 관측: 체인의 첫 10단이 `P a s s w o r d` + 공백 + `i` + `s `를 순서대로 잇는다(디컴파일의 인자 순서는 (dest, p2, p3)이며 결과 = p3 & p2).
- 원인: VarCat 호출은 먼저 push한 인자가 왼쪽 피연산자. 이 규칙으로 10단이 정확히 `Password is `가 되므로 규칙이 맞다고 판단. 확인(문자열이 의미를 이룸)
- 결과: 나머지 5단 = `Password is ` + [+0x38] + "s" + [+0x3c] + "C" + [+0x40] = `Password is LIstenCare`. 확인(정적 계산)
- StrCat(0x404110)도 같은 규칙(먼저 push한 BSTR가 왼쪽): "te" + "n" = "ten". 추정(StrCat 인자 순서는 VarCat과 같다고 가정)

## 도출 값
- 플래그 텍스트: **`Password is LIstenCare`** -> 값 **`LIstenCare`**. 확인(정적 계산), 실행으로 관측하지 않음.

## 미확인
- 0x4040c0 핸들러의 이벤트(필드 +0x3c가 언제 세트되는지).
- 검사 B(FUN_00404170)의 역할, README의 "여러 1분 검사" 중 위 두 곳 외의 검사 존재 여부.
- 플래그가 캡션에 표시되는지(vtable +0x54 슬롯 의미는 추정).
