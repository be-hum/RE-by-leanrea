<!-- 목적: age 분석 노트 단계 03 (흐름 (근거 주소)). 출처: notes/age.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 흐름 (근거 주소)
1. `main.encryptPass` (0x1df0c0)
   - `main.passphrasePromptForEncryption` 호출. 빈 값이면 "passphrase can't be empty" 오류.
   - `NewScryptRecipient`가 인라인됨: newobject에 비밀번호 슬라이스 저장, `[rax+0x18] = 0x12`(work factor 18) (0x1df1f9).
   - `main.encrypt`(0x1df300)로 recipient 1개 전달.
2. `main.encrypt`: `filippo.io/age.Encrypt` 호출 후 `io.copyBuffer`로 입력을 반환된 writer에 복사, 마지막에 Close.
3. `age.Encrypt` (0x18f780)
   - `crypto/rand.Read` 16바이트 = 파일 키 (0x18f7e5 `ebx=0x10`).
   - recipient마다 `wrapWithLabels` -> `(*ScryptRecipient).WrapWithLabels` -> `Wrap`.
   - `headerMAC`, `(*Header).Marshal`로 헤더 출력.
   - `crypto/rand.Read` 16바이트 = nonce, 출력에 기록("failed to write nonce").
   - `streamKey(fileKey, nonce)`로 페이로드 키 생성 후 스트림 writer 생성(NewWriter는 인라인으로 보임, 0x18fc2d "chacha20poly1305: bad key length").
4. `(*ScryptRecipient).Wrap` (0x190f40)
   - salt 16바이트 `crypto/rand.Read`.
   - stanza 타입 "scrypt"(len 6, 0x19100f), 인자로 salt와 work factor(`strconv.FormatInt` base 10, 0x190fea).
   - scrypt salt = "age-encryption.org/v1/scrypt"(28B, 0x1910a7~0x1910da 즉시값) + salt 16B = 44B(`ebx=0x2c`).
   - `scrypt.Key(pass, salt44, N=1<<workFactor(0x19113a shl), r=8(r10), p=1(r11), keyLen=?)` (0x19116a).
   - `aeadEncrypt(scrypt키, fileKey)`로 파일 키 감싸기.
5. `streamKey` (0x190da0): `hkdf.New`, info "payload"(0x190deb/0x190df1 겹친 4바이트 저장), 32바이트 출력(`0x20`).
6. `headerMAC` (0x190ba0): `hkdf.New`, info "header"(0x190bde + 0x190be4), 32바이트 키 -> `hmac.New` -> `MarshalWithoutMAC` 결과에 대한 MAC.
7. `stream.(*Writer).flushChunk` (0x18a420): 버퍼 0x10010 = 64KiB 평문 + 16B 태그, nonce 길이 12(`r8d=0xc`), AEAD Seal은 인터페이스 호출(`call rdx`).
