<!-- 목적: minisign(B-002) 채점 후 재분석. 04-source-grading.md 누락 2(메시지 로드 방식)와 4(-o 시 정보 출력 대상)를 바이너리에서 다시 찾는다. 소스를 본 뒤의 재분석. 근거: targets/minisign/result/01-objdump.txt, 02-main-ann.txt. -->
# minisign 재분석

## 누락 4: `-o`일 때 정보 출력이 stderr
- 관측: `cmp DWORD PTR [rbp-0x64],0x0`(0x103db0d) 후 `mov eax,0x10480e0; mov ecx,0x1047f00; cmove rcx,rax; mov [rbp-0x70],rcx`(0x103db11~0x103db1f). `[rbp-0x64]`는 옵션 `o` 분기에서 1로 설정(0x103d628, 기본 0은 0x103d556).
- 관측: 오류 출력은 `mov edi,0x1047f00`을 FILE* 인자로 쓰는 호출(0x103e241 키 ID 불일치 메시지 직전, 0x103e191 "Duplicate option", 0x103e2d2 "Key generation aborted") -> 0x1047f00 = stderr, 0x10480e0 = stdout(musl FILE 객체, 추정).
- 결과: `-o` 없음(0): `cmove`가 stdout(0x10480e0) 선택, `-o` 있음: stderr 유지 -> 최종 성공 메시지 `fprintf([rbp-0x70], ...)`(0x103e09e)가 `-o`일 때 stderr로 간다(소스 m.c:449-451과 일치).
- 판정: **잡힘**(M-003: `cmove` 두 후보 주소와 조건 변수를 해석).

## 누락 2: 메시지 로드 방식 (`0x103ec09`)
- 관측: 세 번째 인자(프리해시 여부, `test edx,edx; je 0x103ecdd`, 0x103ec2f)로 분기.
- 프리해시 쪽(0x103ec37~0x103ecdb): `fopen`(0x10422d3), 스택 64KiB(`sub rsp,0x101c0`, 읽기 크기 `mov edx,0x10000`, 0x103ec69) 읽기 루프(`fread` 0x10425a5 -> 갱신 0x103cd68), `feof` 확인(0x104203f), `fclose`(0x1041deb), 출력 버퍼 `malloc(0x40)`(0x103fcd0), 최종화(0x103cd72), 길이 64.
- 일반 쪽(0x103ecdd~): `fopen`, `fseek`(0x1042728), `ftell`(0x10427dd) 결과 -1 확인(`cmp rax,-1`, 0x103ed09), 음수 확인(`js`), `malloc`(길이), `rewind`(0x1042e78), `fread(…,1항목)` 반환 1 확인(`cmp rax,1`, 0x103ed47), 실패 시 "Error while loading the message".
- 결과: 프리해시는 64KiB 청크 스트리밍 해시, 레거시는 전체 길이를 알아 한 번에 읽는다(소스 m.c:76-132와 일치).
- 판정: **잡힘**(M-003, 호출 목록에서 이름 없는 libc 호출을 인자 상수로 해석: `0x10000`, `-1`, `1`).

## 누락 1·3
- 누락 1(공개키 파일 1행 무시), 누락 3(`trim` 의미): 이번에는 수행하지 않음 -> **미확인으로 유지**.
