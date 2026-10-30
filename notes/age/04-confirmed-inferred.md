<!-- 목적: age 분석 노트 단계 04 (확인/추정 구분). 출처: notes/age.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 확인/추정 구분
- 확인(코드 근거): 위 1~7의 호출 순서, 크기 상수, 라벨 문자열, work factor 18, scrypt r=8 p=1.
- 추정:
  - `call rdx/rcx/r10`은 인터페이스(cipher.AEAD, io.Writer) 호출로 해석. 대상 타입은 추적하지 않음.
  - HKDF의 해시가 SHA-256인지(인자로 넘기는 함수 포인터 미확인).
  - scrypt keyLen 32(스택 인자라 미확인).
  - 마지막 청크 플래그(`setLastChunkFlag`)와 nonce 증가(`incNonce`) 형식.
- 열린 질문: 헤더 텍스트 형식("age-encryption.org/v1" 버전 줄, `-> scrypt <salt> <wf>` 스탠자, `---` MAC 줄)의 직렬화 세부는 `format.(*Header).Marshal`을 아직 안 읽음.
