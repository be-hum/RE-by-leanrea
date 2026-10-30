<!-- 목적: Aegis Authenticator(B-005) 블라인드 분석 단계 01 (대상 식별). 입력: targets/aegis/aegis-v3.4.3.apk. 생성: curl, sha256sum, unzip -l, jadx --no-res. 이 단계까지 소스 tarball은 받았으나 풀지 않았다. -->
# Aegis Authenticator (B-005, TOTP 코드 생성)
- 진위: 미확인(릴리스에 체크섬·서명 검증값 없음, APK 서명 미확인)

- 출처: GitHub release `v3.4.3` `aegis-v3.4.3.apk` (6,881,897바이트)
  - sha256 `fa091c91912c0d56ec3553394fac4158f9a9d178e93bcbb35419601d788cb528`. 릴리스에 별도 체크섬·서명 검증값 없음, 출처 진위와 APK 서명 **미확인**.
- 형식: Android APK, `classes.dex`(4.3MB), `classes2.dex`(0.5MB), `lib/*/libimage_processing_util_jni.so`·`libsurface_util_jni.so`(CameraX 계열), 네이티브 OTP 코드 없음.
- 디컴파일: `jadx --no-res`(`targets/aegis/result/jadx/`), 3,075개 `.java`, 오류 31개(`result/00-jadx.log`). 패키지 이름 `com.beemdevelopment.aegis.*`는 보존.
- 범위: TOTP 코드 생성(시크릿 -> HMAC -> 자리수 변환). 볼트 암호화, 가져오기, UI는 범위 밖.

## 식별 방법
- 관측: 패키지·클래스 이름이 대부분 보존 -> `otp/` 디렉터리에 `OtpInfo`, `TotpInfo`, `HotpInfo`, `SteamInfo`, `YandexInfo`, `MotpInfo`.
- 관측: R8 코드 병합: `TotpInfo.getOtp`가 `kotlin.ExceptionsKt.generateOTP(...)`를 호출, 해당 클래스는 이름과 무관한 정적 메서드를 다수 포함. `fromJson`은 `kotlin.time.DurationKt.decode`(Base32 디코딩)를 호출. -> 조치: 이름을 믿지 않고 메서드 본문으로 역할 판정(M-206). `OTP`는 `com.beemdevelopment.aegis.crypto.otp.OTP`로 이름 보존되나 `$r8$classId` 스위치로 여러 클래스가 합쳐져 있음.
