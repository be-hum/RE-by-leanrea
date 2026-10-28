# RE-by-leanrea

배포된 바이너리/펌웨어를 정적 분석해 구조와 동작을 파악하는 Claude Code 워크스페이스.
`leanrea` 스킬로 빠르게 개요를 잡고, 자세히 볼 지점만 Ghidra headless로 질의한다.

## 분석 흐름

1. **Triage (leanrea)**: `file`, `readelf`, `nm`, `strings`, `objdump`, `r2` 등 로컬 CLI로 형식 판별, inventory, 개요 파악.
2. **Deep dive (Ghidra headless)**: 동작을 이해하려는 지점의 디컴파일과 호출 관계가 필요할 때만 `tools/ghidra/query.sh` 호출. 결과의 호출 관계를 따라 반복.
3. **정리**: 결과를 `notes/<name>.md`에 기록.

## 요구 사항

- Linux 또는 WSL2
- JDK 25 (`sudo apt install openjdk-25-jdk`)
- Ghidra 12.2 이상, `~/tools/ghidra`에 설치 (다른 위치면 `GHIDRA_HOME` 지정)
- 기본 JDK가 25가 아니면 `$GHIDRA_HOME/support/launch.properties`의 `JAVA_HOME_OVERRIDE`에 JDK 25 경로 지정
- [Claude Code](https://claude.com/claude-code)와 `leanrea` 스킬 (이 저장소에 포함되지 않음)

## 사용법

```sh
mkdir -p targets/foo && cp /path/to/binary targets/foo/

# 질의: 함수명, 0x주소, str:문자열 (여러 개 가능)
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
- import 때 `FixEntry.java`가 stripped 바이너리의 `main`처럼 entry에서만 참조되는 코드를 함수로 복구한다.
- 결과는 `analysis/<name>/<binary>/query-*.txt`에도 저장된다. stdout은 축약본(함수당 200줄, `QUERY_MAX_LINES`).
- 같은 대상에 대한 동시 호출은 순서대로 실행된다.

전체 덤프가 필요하면:

```sh
tools/ghidra/analyze.sh targets/foo/binary
# -> analysis/foo/binary/{functions.tsv,strings.tsv,imports.tsv,decompiled.c}
```

## 디렉토리

| 경로 | 내용 | git |
|---|---|---|
| `targets/` | 분석 대상 원본 (`targets/<name>/`) | 제외 |
| `analysis/` | Ghidra 프로젝트 DB, 질의 결과, 작업 파일 | 제외 |
| `notes/` | 대상별 분석 결과 | 포함 |
| `tools/ghidra/` | `query.sh`, `Query.java`, `FixEntry.java`, `analyze.sh`, `ExportAll.java` | 포함 |

## 원칙

- 승인된 대상만 분석한다.
- 대상 파일은 실행하지 않는다 (정적 분석만).

## License

MIT
