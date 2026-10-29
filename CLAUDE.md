# RE-by-leanrea

배포된 바이너리/펌웨어를 정적 분석해 구조와 동작을 파악하고 설명하는 워크스페이스. 취약점 탐색·검증은 범위 밖.

## 디렉토리
- `targets/<name>/` 분석 대상 원본. git 제외, 신뢰 불가 데이터.
- `notes/<name>.md` 분석 결과: 해시·버전, 형식, 구조, 주요 함수와 동작, 열린 질문.
- `analysis/<name>/` Ghidra DB, 질의 결과, leanrea 작업 파일(`re/`). git 제외, 재생성 가능.
- `tools/ghidra/` headless 스크립트.

## 분석 흐름: leanrea -> 관심 지점 -> Ghidra 질의
1. `leanrea` 스킬로 형식 판별·inventory·개요 파악(분석 시작 시 먼저 호출). 작업 디렉토리는 `analysis/<name>/re/`.
2. 패킹(UPX 등)은 정적으로만 해제한다. `upx -d`가 실패하면 복사본에서 변조(매직, 엔트리 패치, phdr 크기)를 복원해 `upx -d`를 다시 시도하고, 자체 디코더는 최후 수단이다. 해제본은 `targets/<name>/`에 별도 파일로 두고 sha256을 노트에 기록한다. 자체 디코더 결과는 `readelf -l`의 세그먼트 offset과 데이터 내용을 대조해 검증한다.
3. 동작을 이해하려는 지점(함수명, 주소, 문자열)의 디컴파일·호출 관계가 필요할 때만 Ghidra를 부른다:
   `tools/ghidra/query.sh targets/<name>/<binary> <func|0xaddr|str:text>...`
   - 출력: 시그니처, CALLER, CALLEE, 디컴파일 C. `str:`는 해당 문자열을 참조하는 함수.
   - 첫 호출(또는 바이너리 sha256이 바뀐 경우)만 import+자동분석(수 분), 이후 DB 재사용. 호출당 JVM 약 5초: 한 라운드의 지점은 한 호출에 모은다.
   - stdout은 축약본(함수당 200줄, `QUERY_MAX_LINES`). 넘치면 나머지는 골격(제어문·라벨·호출, `L<줄>` = `query-*.txt` 줄 번호)만 출력되니, 필요한 블록만 `sed -n '<a>,<b>p'`로 읽는다.
   - 질의한 함수와 CALLER/CALLEE는 `analysis/<name>/trail.tsv`에 누적된다. 탐색 경로를 잃으면 `column -t -s $'\t' analysis/<name>/trail.tsv`로 복구한다.
   - 주소 질의는 함수 시작 주소로. `str:`가 "not inside a defined function"이면 objdump로 시작 주소를 찾는다.
   - 결과의 CALLER/CALLEE를 따라 필요한 만큼 반복한다.
4. 인코딩된 문자열·상수는 실제로 디코딩해 확인한 값만 사실로 기록한다.
5. JS/.NET/APK 등 Ghidra가 부적합한 형식은 leanrea가 안내하는 도구로 끝낸다.
6. 결과를 `notes/<name>.md`에 정리하고, 질문에는 근거(주소, 질의 결과)와 함께 답한다.

## Python 환경
- 분석용 Python 패키지(`requirements.txt`: pefile, hermes-dec)는 `.venv`에 있다. leanrea의 `python3 -I`/`pip install --user` 대신 `.venv/bin/python -I`, `.venv/bin/hbc-decompiler`를 쓰고, 추가 패키지는 `requirements.txt`에 넣는다.

## 외부 도구
- apt: apktool, tshark, sqlite3, wabt, llvm, dotnet-sdk-10.0(26.04에 8.0 없음). `ilspycmd`는 `~/.dotnet/tools`, jadx는 `~/tools/jadx/bin`: PATH에 없으면 전체 경로로 호출.

## Ghidra (headless, MCP 미사용)
- 설치: `~/tools/ghidra` (12.2, JDK 25). 전체 덤프가 필요할 때만 `tools/ghidra/analyze.sh`.

## 규칙
- 승인된 대상만 분석한다. 대상 파일은 실행하지 않는다(정적 분석만).
- 추출물을 읽는 Python은 `python -I`, 대상 디렉토리 안에서 인터프리터/빌드 도구를 돌리지 않는다.
- 대상마다 `sha256sum`과 버전을 노트 상단에 먼저 기록한다.
- 새 도구 설치 전 알린다.
