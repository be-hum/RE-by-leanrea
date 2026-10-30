<!-- 목적: Adventure 분석 노트 단계 02 (구조). 출처: notes/Adventure.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
## 구조
- 게임 클래스 vtable(file 0x10e84): +0x18 `0x404680` 리소스 로드(wooyaggo/bullet/devil/gg.png), +0x1c `0x4043a0` = `rand()%(b-a+1)+a`, +0x20 `0x405890` = rol32.
- `FUN_004032e0` 초기화: `srand(100)`, 킬 카운터 u64 `+0xb8` = 0xaaaaaaaaaaaaaaaa(점수 = 초기값 - 카운터, 위장), flag 상태 u32 lo/hi[5] `+0x88` 0으로.
- `FUN_00403890` 프레임 갱신:
  - 매 프레임 `rand(1,50)==5`이고 슬롯(30개 원형) 비면 적 생성: `x=rand(0,W)`, `dir=rand(1,2)`, `sx=rand(1,4)`, `sy=rand(4,10)`.
  - 적이 화면 아래로 나가면 게임오버(`+0x8c=1`). 즉 모든 적을 처치해야 함.
  - 처치 시(0x403c8e): `lo[sx]^=dir; hi[sx]^=dir`, 카운터 감소. 점수 0xddb(3547)에서 상수 C1 XOR 후 lo/hi[1..4] 32바이트를 "Flag1 is "로 출력, 0x31159cd(51468749)에서 C2 XOR 후 "Flag2 is ". 이후(0x4040fe) `lo[sx]=rol(lo[sx],sx); hi[sx]=rol(hi[sx],sy)`.
- 결론: flag는 MSVC rand(seed 100) 스트림으로 결정되는 적 생성 순서에만 의존(모두 처치 전제).
