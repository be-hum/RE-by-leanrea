<!-- 목적: FlashEncrypt 분석 노트 단계 01 (overview). 출처: notes/FlashEncrypt.md(이전 단일 노트)의 해당 절을 그대로 분할 이전. -->
# reversing.kr Flash Encrypt

- flashenc.swf sha256 `c65993b134cd1b77d3d0b9788ccaf0b038ddd3cec9ed81bdcb5eb0d802d96ba6`
- 형식: CWS(zlib) SWF v9, AVM1(AS2). 7프레임, 프레임마다 입력 필드(첫 프레임 var `spw`, 이후 `spwd`)와 DefineButton2 하나.
- 도구: JPEXS 없음, 직접 작성한 SWF 파서 + AVM1 에뮬레이터(`tmp/reversing.kr/FlashEncrypt/swf.py`, `emu.py`).
