# RE-by-leanrea

배포된 바이너리/펌웨어를 정적 분석해 취약점을 찾는 Claude Code 워크스페이스.
`leanrea` 스킬로 빠르게 triage하고, 의심 지점에 대해서만 Ghidra headless로 깊게 질의한다.

## 분석 흐름

1. **Triage (leanrea)**: `file`, `readelf`, `nm`, `strings`, `objdump`, `r2` 등 로컬 CLI로 형식 판별, inventory, 공격면 파악. 의심 지점(함수명, 주소, 문자열)을 `notes/<name>.md`에 기록.
2. **Deep dive (Ghidra headless)**: 의심 지점의 디컴파일과 호출 관계가 필요할 때만 `tools/ghidra/query.sh` 호출. 결과에서 나온 새 의심 지점으로 반복.
3. **검증**: `fp-check`로 오탐 제거 후 `findings/`에 리포트.

## 요구 사항

- Linux 또는 WSL2
- JDK 25 (`sudo apt install openjdk-25-jdk`)
- Ghidra 12.2 이상, `~/tools/ghidra`에 설치 (다른 위치면 `GHIDRA_HOME` 지정)
- 기본 JDK가 25가 아니면 `$GHIDRA_HOME/support/launch.properties`의 `JAVA_HOME_OVERRIDE`에 JDK 25 경로 지정
- [Claude Code](https://claude.com/claude-code)와 `leanrea` 스킬 (이 저장소에 포함되지 않음)

## 사용법

```sh
mkdir -p targets/foo && cp /path/to/binary targets/foo/

# 의심 지점 질의: 함수명, 0x주소, str:문자열 (여러 개 가능)
tools/ghidra/query.sh targets/foo/binary parse_header 0x401a20 str:Content-Length
```

출력 (각 함수마다):

```
==== QUERY <query> -> <function> @ <entry>
SIG     <prototype>
CALLER  <call site> <caller>
CALLEE  <entry> <callee> [ext]
<decompiled C>
```

- 첫 호출에서만 import와 자동 분석을 수행하고, 이후에는 `analysis/<name>/ghidra` 프로젝트를 read-only로 재사용한다.
- 결과는 `analysis/<name>/<binary>/query-<timestamp>.txt`에도 저장된다.
- stripped 바이너리에서 함수로 인식되지 않은 주소는 메모리상에서만 함수를 생성해 디컴파일한다 (DB에 저장하지 않음).

전체 덤프가 필요하면:

```sh
tools/ghidra/analyze.sh targets/foo/binary
# -> analysis/foo/binary/{functions.tsv,strings.tsv,imports.tsv,decompiled.c}
```

## 디렉토리

| 경로 | 내용 | git |
|---|---|---|
| `targets/` | 분석 대상 원본 (`targets/<name>/`) | 제외 |
| `analysis/` | Ghidra 프로젝트 DB, headless 산출물 | 제외 |
| `notes/` | 대상별 분석 노트 | 포함 |
| `findings/` | 검증된 취약점 리포트 | 포함 |
| `tools/ghidra/` | `query.sh`, `Query.java`, `analyze.sh`, `ExportAll.java` | 포함 |

## 원칙

- 승인된 대상만 분석한다 (자체 소유, 버그바운티 범위, CTF, 공개 연구).
- 대상 파일은 실행하지 않는다. 동적 분석은 격리 환경에서만.
- PoC는 크래시/영향 증명까지만 작성한다.

## License

MIT
