<!-- 목적: age 분석 노트 단계 06 (소스 대조 채점 (FiloSottile/age v1.2.1, commit 482cf6f, `analysis/age/src`)). 출처: notes/age.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 소스 대조 채점 (FiloSottile/age v1.2.1, commit 482cf6f, `analysis/age/src`)
배포판 빌드라 Debian 패치 가능성은 있으나, 대조 범위에서 불일치는 없었음.

| # | 바이너리 해석 | 소스 | 판정 |
|---|---|---|---|
| 1 | encryptPass: 프롬프트, 빈 값 오류, wf 18, encrypt 호출 | 일치. 빈 값 검사는 `NewScryptRecipient`(인라인) 안 | 맞음(위치 세부 보정) |
| 1a | 0x1df260 `call rcx` | `testOnlyConfigureScryptIdentity(r)`: 전역 함수 변수(테스트용 훅, 기본 no-op) | 누락. 인터페이스 호출로 뭉뚱그림 |
| 2 | encrypt: Encrypt -> io.Copy -> Close | 일치. 단 `withArmor`(r10 bool 인자) 분기와 armor writer의 defer Close 존재 | 부분 누락 |
| 3 | Encrypt: 파일 키 16B, wrap, headerMAC, Marshal, nonce 16B, streamKey, NewWriter 인라인 | 일치 | 맞음 |
| 3a | `sort.Strings` 호출 | recipient 라벨 정렬 후 recipient 간 라벨 호환성 검사("incompatible recipients") | 호출은 봤으나 의미 미해석 |
| 4 | Wrap: salt 16B, stanza "scrypt", 인자 salt+wf(10진), 라벨+salt 44B, scrypt N=2^wf r=8 p=1, aeadEncrypt | 일치. salt 인자는 base64(`format.EncodeToString`), wf는 `strconv.Itoa` | 맞음 |
| 4a | scrypt keyLen 32 (추정) | `chacha20poly1305.KeySize` = 32 | 추정 적중 |
| 4b | aeadEncrypt | 고정 0 nonce(12B) 사용, 키가 매번 새 salt로 유도되므로 안전하다는 설계 주석 | 누락 |
| 4c | WrapWithLabels: rand 호출, hex 문자열 | 16B 난수를 hex 라벨로 반환(scrypt는 다른 recipient와 섞이지 않게 하는 고유 라벨) | 관찰만, 의미 미해석 |
| 5 | streamKey: HKDF info "payload", 32B | `hkdf.New(sha256.New, fileKey, nonce, "payload")` | 맞음, SHA-256 추정 적중 |
| 6 | headerMAC: HKDF info "header", HMAC, MAC 제외 헤더 | salt nil, HMAC-SHA256, 대상은 intro+스탠자+"---" | 맞음 |
| 7 | flushChunk: 64KiB+16B, nonce 12B, Seal 인터페이스 | 일치 | 맞음 |
| 7a | 마지막 청크/nonce 증가 (미확인) | nonce = 11B 빅엔디언 카운터 + 마지막 바이트 last 플래그 | 열린 질문이었음 |
| 8 | 헤더 형식 (열린 질문) | `age-encryption.org/v1\n`, `-> scrypt <b64salt> <wf>` 스탠자, `--- <b64 MAC>\n` | 열린 질문이었음 |

- 오답(틀린 단정): 없음.
- 누락: 1a, 2(armor), 3a, 4b, 4c. 공통 원인은 "알려진 함수 호출만 따라가고, 간접 호출(전역 함수 변수), bool 인자 분기, 이름은 보였지만 의미를 모르는 호출을 해석하지 않은 것".
- 추정 2건(SHA-256, keyLen 32)은 적중했으나, 바이너리 근거로 확인한 것은 아님.
