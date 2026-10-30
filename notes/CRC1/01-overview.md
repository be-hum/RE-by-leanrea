<!-- 목적: CRC1 분석 노트 단계 01 (overview). 출처: notes/CRC1.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
# reversing.kr CRC1

- CRC.exe sha256 `577faed446742cb683aa28196158ae76bef74906184d959589b69e25388b3936`
- CRC1.zip sha256 `f068bac2d327525b117652dc2b933bae2c22f4f3d82b4b2b62b3b9def5cd97bf` (CRC.exe 139264 B, 2013-04-10)
- 형식: PE32 GUI, i386, MSVC 런타임, 비패킹. import: USER32(Dialog*, GetDlgItemTextA, SetDlgItemTextA, MessageBeep), GDI32, KERNEL32.
