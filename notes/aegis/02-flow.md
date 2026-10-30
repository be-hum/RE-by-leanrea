<!-- 목적: Aegis 블라인드 분석 단계 02 (TOTP 코드 생성 흐름). 근거는 targets/aegis/result/jadx/sources/ 아래 디컴파일 파일과 줄. 함수 이름은 R8 병합 이름 그대로. -->
# 흐름: 볼트 항목 JSON -> OtpInfo -> HMAC -> 코드

경로는 `result/jadx/sources/` 기준.

## 단계 1: 항목 로딩 `com/beemdevelopment/aegis/otp/OtpInfo.fromJson(type, info)` (OtpInfo.java:22-)
- 관측: `secret`을 `kotlin.time.DurationKt.decode`로 디코딩(DurationKt.java:291), 본문은 `BaseEncoding$StandardBaseEncoding.BASE32.decode(str.toUpperCase(Locale.ROOT))`. 오류는 `EncodingException`. -> 결과: 시크릿은 Base32 문자열, 대문자로 바꿔 디코딩.
- 관측: `algo`, `digits`를 읽고, `type`이 `motp`가 아니면서 `algo`가 `MD5`이면 `SHA1`로 바꿈(OtpInfo.java:29-32). -> 결과: MD5는 mOTP에서만 허용.
- 관측: `type` 문자열 스위치: `totp`, `hotp`, `steam`, `yandex`, `motp`. `totp`이면 `new TotpInfo(digits, info.getInt("period"), algo, secret)`.

## 단계 2: 제약
- 알고리즘: `setAlgorithm`은 접두 `Hmac`를 떼고 대문자로 바꾼 값이 `SHA1`, `SHA256`, `SHA512`, `MD5` 중 하나여야 함(OtpInfo.java:122-130). `getAlgorithm()`은 `"Hmac"+알고리즘`.
- 자리수: `1 <= digits <= 10`(OtpInfo.java:133-136). 기본 생성자는 `SHA1`, 6자리(OtpInfo.java:18).
- 주기: `TotpInfo.setPeriod`: `0 < period <= 2147483`(TotpInfo.java:38-43), 기본 30(TotpInfo.java:13).

## 단계 3: 카운터 `TotpInfo.getOtp()` (TotpInfo.java:25-27, 54-61)
- 관측: `getOtp()` = `getOtp(System.currentTimeMillis() / 1000)`, `getOtp(t)` = `generateOTP(secret, "Hmac"+알고리즘, digits, (long) Math.floor(t / (double) period))`. 시크릿이 비어 있으면 `OtpInfoException("Secret is empty")`.
- 결과: 카운터 = floor(유닉스 초 / 주기).

## 단계 4: HMAC `ExceptionsKt.getHash` (ExceptionsKt.java:~516)
- 관측: `SecretKeySpec(secret, "RAW")`, 카운터를 `ByteBuffer.allocate(8).order(BIG_ENDIAN).putLong(counter)`로 8바이트화, `Mac.getInstance(알고리즘).init(키).doFinal(8바이트)`.

## 단계 5: 동적 절단 `ExceptionsKt.generateOTP` (ExceptionsKt.java:522-526)
- 관측: `offset = hash[last] & 0x0F`; 코드 = `((hash[offset] & 0x7F) << 24) | ((hash[offset+1] & 0xFF) << 16) | ((hash[offset+2] & 0xFF) << 8) | (hash[offset+3] & 0xFF)`; `new OTP(code, digits, 0)`.

## 단계 6: 문자열화 `OTP.toString` (crypto/otp/OTP.java, case 0)
- 관측: `Long.toString(code % (int) Math.pow(10.0, digits))`를 왼쪽 0 채움으로 `digits`자리 맞춤.
- Steam 변형: `toSteamString()`은 `"23456789BCDFGHJKMNPQRTVWXY"`에서 `code % 26`을 `digits`번 뽑아 이어 붙임(OTP.java:15-21). `SteamInfo`의 경로는 세부 미확인.

## 미확인
- `HotpInfo` 카운터 증가 방식(저장 시점), `YandexInfo`(PIN과 해시 변형), `MotpInfo` 본문
- 볼트 JSON 스키마의 다른 필드(그룹, 아이콘)
- `Math.pow` 결과를 `int`로 캐스팅할 때 digits=10에서의 오버플로 영향
