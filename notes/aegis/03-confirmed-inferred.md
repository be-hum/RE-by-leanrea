<!-- 목적: Aegis 블라인드 분석 단계 03 (확인/추정/미확인). 02-flow.md 항목을 채점 단위로 나눈 표. 소스 대조 전 상태. 디컴파일 코드를 직접 읽은 항목은 확인으로 표시. -->
# 확인 / 추정 / 미확인 (소스 열기 전)

## 확인 (디컴파일 코드를 줄 단위로 읽음)
1. 시크릿 = Base32(대문자화 후 디코딩)
2. 알고리즘 허용 집합 SHA1/SHA256/SHA512/MD5, MD5는 mOTP 외에는 SHA1로 치환
3. 자리수 1~10, 기본 SHA1·6자리
4. 주기 1~2147483, 기본 30
5. 카운터 = floor(unix초 / 주기), 8바이트 big-endian
6. HMAC(키=시크릿 RAW, 메시지=카운터 8바이트)
7. 동적 절단: 오프셋 = 마지막 바이트 & 0xF, 상위 비트 마스크 0x7F
8. 코드 mod 10^digits, 왼쪽 0 채움
9. 시크릿이 비면 예외 "Secret is empty"
10. 지원 타입 totp/hotp/steam/yandex/motp, Steam 알파벳 26자

## 추정
- 이름이 어긋난 클래스(`kotlin.ExceptionsKt`, `kotlin.time.DurationKt`)는 R8이 병합한 Aegis 코드
- 현재 시각은 단말 `System.currentTimeMillis()`

## 미확인
- HOTP 카운터 저장 방식, Yandex·mOTP 세부
- 볼트 복호화 경로
- digits=10 오버플로 영향
