<!-- 목적: age 분석 노트 단계 01 (overview). 출처: notes/age.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
# age (`age -p` 비밀번호 기반 암호화 흐름)
- 진위: 미확인(노트에 릴리스 체크섬·서명 대조 기록 없음, 2026-10-30 점검)

- 출처: Ubuntu 패키지 `age 1.2.1-1build1`, `/usr/bin/age`를 `targets/age/age`로 복사
- sha256 `00c07670d548aa01705923fbbecbcd6edb76a65bd73e1b5644fad0c4a60bf678`
- 형식: ELF64 x86-64 PIE, stripped, Go go1.25.0, `-trimpath`, CGO_ENABLED=1. buildinfo에 모듈 버전 없음(배포판 빌드).
- 범위: `age -p`(passphrase) 암호화 경로만. 복호화, X25519, SSH, 플러그인은 범위 밖.
