<!-- 목적: Adventure 분석 노트 단계 01 (overview). 출처: notes/Adventure.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
# reversing.kr Adventure

- Adventure.zip sha256 `a6e49b497e423d98e657fcfe9beafb76c8746afb822020671b2df756a2abc11f`
- Adventure_1.0.0.0_Win32.appx sha256 `144b9909a579f3427f9c85e0e2d8df3e6eab930c7856b75d9dd98418ad868266`
- Adventure.exe (appx 내부, `targets/reversing.kr/Adventure/Adventure.exe`로 복사) sha256 `44035d57bf675c14a28e018b5d5ea55027c9c117376f373a7c1f944d4b3c4e4c`
- 형식: PE32 GUI i386, UWP C++/CX DirectX 앱(vccorlib110, d2d1, d3d11, DWrite). 비패킹.
- ReadMe: `flag is lowercase(md5(flag1 + flag2))`
