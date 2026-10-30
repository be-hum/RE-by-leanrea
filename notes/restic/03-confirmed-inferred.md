<!-- 목적: restic 블라인드 분석 단계 03 (확인/추정/미확인 분류). 02-flow.md의 항목을 채점 단위로 나눈 표. 소스 대조 전 상태. -->
# 확인 / 추정 / 미확인 (소스 열기 전)

## 확인
1. 호출 순서 SearchKey -> OpenKey -> LoadKey -> KDF -> (*Key).Open -> json.Unmarshal -> (*Key).Valid (result/03, 04)
2. KDF에서 salt 길이 64 필수, scrypt 출력 64바이트 (0x7e9ed2, 0x7ea086)
3. scrypt는 `x/crypto/scrypt.Key`, 파라미터 검증은 `simple-scrypt` `Params.Check`
4. 출력 분할: [0:32] -> +0x20, [32:64] -> +0..+0x20 (0x7ea0b6~0x7ea0ed)
5. Open: Valid 선검사, nonce 16B, 암호문 > 16B 조건, poly1305Verify 후 AES-256 + CTR
6. 힌트 키 경로(Find -> OpenKey)와 전체 순회 경로(클로저 func1)로 나뉨, 로그 문자열 6종 디코딩
7. 함수 entry 보정값 0 (non-PIE)

## 추정
- 출력 분할의 의미: [32:64]=MAC 키(K,R), [0:32]=AES 키 (필드명 순서 미확인)
- MAC = Poly1305-AES(nonce를 AES-128로 암호화해 s 생성), 태그는 암호문 끝 16B
- 순회는 첫 성공 시 cancel로 중단
- key 파일 JSON 필드 구성 (created/username/hostname/kdf/N/r/p/salt/data)

## 미확인
- Init/AddKey가 기본으로 쓰는 N, r, p 값 (범위 밖 함수 Init/AddKey를 읽지 않음)
- 비밀번호가 틀렸을 때 반환 오류 종류와 순회 계속 여부 (`errors.Is` 대상)
- 태그 비교가 덮는 바이트 범위
- repository.(*Key).Valid의 두 번째 검사 대상
- 최대 시도 key 수 제한 유무 (`MaxKeys` 문자열은 있으나 이 경로 사용 미확인)
