<!-- 목적: Aegis(B-005) 블라인드 분석 노트 01~03을 소스(analysis/aegis/src, 태그 v3.4.3)와 대조한 채점. 근거는 소스 파일:줄과 디컴파일 파일. 소스는 이 단계에서 처음 풀었다. -->
# Aegis B-005 소스 채점

소스: `analysis/aegis/src.tar.gz`(태그 v3.4.3)를 `analysis/aegis/src`에 풀었다. 약어: `otp/`=`app/src/main/java/com/beemdevelopment/aegis/otp/`, `crypto/otp/`=`.../crypto/otp/`.

## 맞음 (10)
| # | 항목 | 소스 | 디컴파일(분석 근거) |
|---|---|---|---|
| 1 | 시크릿 Base32(대문자화 후 디코딩) | encoding/Base32.java:15 | DurationKt.java:291 |
| 2 | 알고리즘 SHA1/SHA256/SHA512/MD5, MD5는 mOTP 외 SHA1 치환 | otp/OtpInfo.java:80, 116-118 | OtpInfo.java:29-32, 122-130 |
| 3 | 자리수 1~10, 기본 SHA1·6 | otp/OtpInfo.java:14-15, 95-97 | OtpInfo.java:18, 133-136 |
| 4 | 주기 1~2147483, 기본 30 | otp/TotpInfo.java:13, 62-70 (`MAX_VALUE/1000`) | TotpInfo.java:38-43 |
| 5 | 카운터 floor(초/주기), 8바이트 big-endian | crypto/otp/TOTP.java:12-13, HOTP.java:33-35 | ExceptionsKt.java getHash |
| 6 | HMAC(키=시크릿 RAW, 메시지=카운터) | crypto/otp/HOTP.java:28-38 | 동일 |
| 7 | 동적 절단 (오프셋 = 마지막 바이트 & 0xF, 0x7F 마스크) | crypto/otp/HOTP.java:19-24 | ExceptionsKt.java:522-526 |
| 8 | 코드 mod 10^digits, 왼쪽 0 채움 | crypto/otp/OTP.java:24-33 | OTP.java case 0 |
| 9 | 빈 시크릿 예외 | otp/OtpInfo.java:33 `checkSecret` | TotpInfo.java:54-57 |
| 10 | 타입 totp/hotp/steam/yandex/motp, Steam 알파벳 | otp/*Info.java ID, OTP.java:7, 38-47 | OtpInfo.fromJson, OTP.java:15-21 |

## 추정 적중 (2)
- `kotlin.ExceptionsKt`, `kotlin.time.DurationKt`는 R8이 병합한 Aegis 코드: 소스에는 `crypto/otp/HOTP`, `encoding/Base32`로 존재.
- 현재 시각 = `System.currentTimeMillis()/1000`: otp/TotpInfo.java:32-34.

## 누락 (0)
- 범위 안 항목 중 놓친 것 없음. 범위 밖 미확인(HOTP 카운터 저장, Yandex, mOTP, 볼트 복호화, digits=10 오버플로)은 채점 제외.

## 오답 (0)

## 집계
- 맞음 10, 추정 적중 2, 누락 0, 오답 0. 기준선 B-001(5, 0)보다 누락 5 감소.
- 해석: jadx가 소스에 가까운 코드를 주므로 정적 분석 난이도가 낮다. 이 사례는 네이티브 형식과 직접 비교하지 말고 APK/DEX 형식의 기준선으로 쓴다. R8 이름 병합은 본문 판정으로 해소(M-206 2번째 사례, M-401 새 항목).
- 추정 -> 확인으로 올라간 M 항목: M-206.

## 되먹임과 재검증
- 오답·누락이 없어 재분석할 고리 없음. 한계: 범위가 단순(표준 RFC 6238/4226 알고리즘)해서 방법론 시험 강도가 낮다. 후속으로 볼트 복호화 경로(scrypt + AES-GCM, 비밀번호 -> 슬롯 -> 마스터 키)를 범위로 삼으면 난이도가 높은 사례가 된다(이번 세션 미수행).
