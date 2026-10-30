<!-- 목적: restic(B-007) 채점 후 재분석. 04-source-grading.md 누락 2(errors.Is의 전역 오류 변수)를 바이너리에서 다시 찾는다. 소스를 본 뒤의 재분석. 근거: targets/restic/result/04, 06, 07. -->
# restic 재분석: ErrUnauthenticated 연결

- 관측: `SearchKey.func1`의 `errors.Is`(0x8cf9d8) 인자는 전역 오류 인터페이스 값(`[0x2183680]`, `[0x2183688]`)(0x8cf9ba, 0x8cf9c1).
- 관측: 같은 전역을 `crypto.init`이 채움(0x7e8c78 `mov [rip..],rax # 0x2183680`, 0x7e8c9b `# 0x2183688`). 값은 `fmt.errorf`(0x7e8c45)로 만든 오류, 메시지 문자열 0x15367e5(길이 0x1e=30) = `ciphertext verification failed`.
- 관측: `crypto.(*Key).Open`은 `poly1305Verify` 실패(`test al,al; jne 0x7e9ac7` 불일치 쪽)에서 같은 전역을 반환 레지스터에 로드(0x7e9aa9 `# 0x2183680`, 0x7e9ab0 `# 0x2183688`).
- 결과: Open이 MAC 검증 실패 시 이 오류를 반환하고, `SearchKey.func1`의 `errors.Is`가 그 오류와 비교한다 -> 비밀번호가 틀리면(복호화 불가) 다음 key로 계속(소스 key.go `ErrUnauthenticated` 처리와 일치). 오류 이름 `ErrUnauthenticated`는 메시지로부터의 해석(변수명은 바이너리에 없음).
- 판정: 누락 2 **잡힘**(M-003: 전역 변수 대상을 초기화 지점과 사용 지점의 주소 일치로 해석).
