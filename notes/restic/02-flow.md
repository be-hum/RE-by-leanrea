<!-- 목적: restic 블라인드 분석 단계 02 (흐름). 근거는 targets/restic/result/NN-* 번호와 주소. 입력: 01-gosym-funcs-raw.tsv, 02-objdump.txt. 생성: tools/scripts/ann.py로 call 대상 주석 후 읽음. -->
# 흐름: 비밀번호 -> key 파일 -> 마스터 키

바이너리 주소는 모두 `repository`=`github.com/restic/restic/internal/repository`, `crypto`=`.../internal/crypto` 기준.

## 단계 1: 진입 SearchKey (0x8cee00, result/03)
- 관측: `restic.Find`(0x821900) 호출, 로그 문자열 "Could not find hinted key %v"(0x1532229), "could not open hinted key %v"(0x153220d), "successfully opened hinted key %v"(0x153ba65) -> 결과: 힌트(key ID 접두)가 주어지면 먼저 Find로 그 key 파일 하나만 `OpenKey`(0x8cefa5)로 시도.
- 관측: 힌트가 없거나 실패하면 `context.WithCancel`(0x8cf015) 후 클로저 `SearchKey.func1`(0x8cf540, result/06)를 목록 순회에 사용. 클로저 안에서 로그 "trying key %q"(0x1519994) -> `OpenKey`(0x8cf711) -> 성공 시 "successfully opened key %v"(0x152e5ad), 실패 시 "key %v returned error %v"(0x152b2e5), `errors.Is`(0x8cf9d8)로 오류 종류 판별.
- 추정: 첫 성공 시 cancel로 순회를 멈춘다(WithCancel 존재 근거, 취소 호출 지점은 미확인). `errors.Is` 대상 오류와 "비밀번호 틀림이면 다음 key로 계속" 여부는 미확인.

## 단계 2: OpenKey (0x8ce8c0, result/03)
- 관측: `LoadKey`(0x8cfa60) -> `makeslice` -> `crypto.KDF`(0x7e9ea0) -> `crypto.(*Key).Open`(0x7e9940) -> `encoding/json.Unmarshal`(0x7c5940) -> `repository.(*Key).Valid`(0x8d0700). 로그 "LoadKey(%v) returned error %v"(0x15342f5), "Unmarshal() returned error %v"(0x1534312).
- 결과: key 파일을 읽어(LoadKey 내부 `LoadRaw` 0x8d8fe0 + `json.Unmarshal`) 구조체로 만들고, 그 안의 KDF 파라미터와 비밀번호로 사용자 키를 유도해, 파일의 `data`를 복호화한 JSON에서 마스터 키를 꺼내 유효성 검사.
- 관측: 바이너리의 json 태그 목록에 `kdf`, `N`, `r`, `p`, `salt`, `data`, `created`, `username`, `hostname`, `mac`, `k`, `r`, `encrypt` 존재(`strings`). 어느 구조체 소속인지는 미확인(추정: key 파일 = created/username/hostname/kdf/N/r/p/salt/data, 마스터 키 = mac{k,r}/encrypt).

## 단계 3: KDF (0x7e9ea0, result/04)
- 관측: 0x7e9ed2 `cmp rsi,0x40` 불일치 시 "scrypt() called with invalid salt bytes (len %d)"(0x155261c) -> salt는 64바이트여야 함.
- 관측: `simple-scrypt.(*Params).Check`(0x7ea00a, 구조체의 dkLen 필드 [rsp+0xb0]=0x40) -> `golang.org/x/crypto/scrypt.Key`(0x7ea086, 출력 길이 0x40) -> 반환 길이가 0x40이 아니면 "invalid numbers of bytes expanded from scrypt(): %d"(0x1555ec2).
- 결과: scrypt(password, salt[64], N, r, p, dkLen=64) 64바이트 출력. 분할(0x7ea0b6~0x7ea0ed): `out[0:32]`를 새 객체 +0x20..+0x40에 memmove(0x20), `out[32:48]`을 객체 +0..+0x10, `out[48:64]`를 객체 +0x10..+0x20에 복사.
- 추정: 객체는 `crypto.Key`이며 +0..+0x20이 MAC 키(K 16B + R 16B), +0x20..+0x40이 AES-256 키. 근거는 아래 단계 4의 Valid 길이 검사(0x20/0x10/0x10)와 AES 키 길이 0x20뿐. 필드명 순서는 미확인.

## 단계 4: Key.Open (0x7e9940, result/04, 05)
- 관측: 먼저 `crypto.(*Key).Valid`(0x7e9d00) 실패 시 "invalid key"(0x1516e07). Valid는 길이 0x20, 0x10, 0x10 검사(0x7e9d09, 0x7e9d2f, 0x7e9d45).
- 관측: nonce(인자) 길이가 0x10이 아니면 "nonce is invalid"(0x151e04a). 암호문 길이가 16 이하이면(0x7e99f4 `cmp rax,0x10; jbe`) "trying to decrypt invalid data: ciphertext too short"(0x1556ec3).
- 관측: `poly1305Verify`(0x7e9aa0) 실패 시 오류 반환(어떤 오류인지는 미확인) 후, 성공해야 `makeslicecopy`(0x7e9b11) -> `aes.NewCipher`(0x7e9b4d, 키 길이 0x20) -> `cipher.NewCTR`(0x7e9bab) -> 복호화. 실패 경로 "unable to create cipher: %v"(0x15306e4)는 `gopanic`(0x7e9c74).
- 관측: `poly1305PrepareKey`(0x7e8de0)가 `aes.NewCipher`(키 길이 0x10, 0x7e8e40) 사용, `poly1305Verify`(0x7e8f00)는 `x/crypto/internal/poly1305.Verify`(0x7e8fb1) 호출.
- 결과(추정): AES-256-CTR 암호화 + Poly1305-AES MAC(encrypt-then-MAC). 입력 배치는 nonce 16B(별도 인자) + 암호문 + 끝 16B 태그. 태그가 끝 16B이고 MAC이 암호문 전체를 덮는지는 미확인(0x7e9a88 `sub r10,rbx` 근거만).

## 단계 5: 마스터 키 검증 (0x8d0700, result/04)
- 관측: `repository.(*Key).Valid`가 `crypto.(*Key).Valid`를 두 번 호출(0x8d071a, 0x8d0734).
- 추정: 마스터 키 구조 안에 `crypto.Key`(복호화 결과 JSON의 `mac`, `encrypt`) 하나와 다른 값을 함께 검사. 두 번째 대상은 미확인.
