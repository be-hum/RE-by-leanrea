# Twist1.step2.exe 용 에뮬 프로필: main 0x401270 ~ 판정(0x4012cf/0x4012df)까지의 범위 밖 callee 스텁과 예외 필터 대행. 스텁 근거는 notes/Twist1/02-emulation-gate.md 관문 3.
from unicorn.x86_const import *
import struct
FAKE_FN, FAKE_ZW = 0x7f000000, 0x7f001000
def setup(ctx):
    uc = ctx.uc
    uc.mem_map(0x7f000000, 0x10000)
    uc.mem_map(0x7ffe0000, 0x1000)                   # KUSER_SHARED_DATA 자리(스텁이 실제로 읽지 않음)
    uc.mem_write(FAKE_ZW, bytes.fromhex('b8 8c 00 00 00 ba 00 03 fe 7f ff 12 c2 14 00 90'.replace(' ', '')))
    uc.mem_write(0x40b964, (0x7e000000).to_bytes(4, 'little'))   # kernel32 모듈 핸들 자리(0x401090 스텁이 이름만 본다)
    uc.mem_write(0x40b968, (0x7e100000).to_bytes(4, 'little'))   # ntdll 모듈 핸들 자리
    uc.mem_write(0x40b970, ctx.text.encode() + b'\0')
    fns = {}
    def add(name, handler):
        a = FAKE_FN + 0x10 * (len(fns) + 1); fns[name] = a; ctx.stubs[a] = handler
    add('SetUnhandledExceptionFilter', lambda c: c.ret(0, 4))
    add('GetCurrentThread', lambda c: c.ret(0xfffffffe, 0))
    def get_ctx(c):                                    # GetThreadContext(h, ctx): 디버그 레지스터 0
        p = c.arg(2); c.uc.mem_write(p + 4, b'\0' * 24); c.ret(1, 8)
    add('GetThreadContext', get_ctx)
    ctx.fns = fns
    def resolve(c):                                    # 0x401090(module, name) cdecl
        n = c.cstr(c.arg(2))
        if n == 'ZwQueryInformationProcess': c.ret(FAKE_ZW, 0)
        elif n in fns: c.ret(fns[n], 0)
        else: c.log.append(f'UNKNOWN IMPORT {n}'); c.ret(0, 0)
    ctx.stubs[0x401090] = resolve
    ctx.stubs[0x401000] = lambda c: c.ret(0, 0)        # PEB Ldr 순회로 0x40b964/0x40b968만 쓰는 모듈 해석기(정적 확인: 0x401000-0x40108a), 두 전역은 위에서 미리 채움
    ctx.stubs[0x4014cd] = lambda c: c.ret(0, 0)        # 0x4011d0이 쓰는 printf 계열(제목 출력), 출력 무시
    ctx.stubs[0x401534] = lambda c: c.ret(0, 0)        # printf: 출력 무시
    def scanf(c):                                      # scanf(fmt, buf) cdecl: 입력은 시작 시 0x40b970에 이미 기록
        c.ret(1, 0)
    ctx.stubs[0x401565] = scanf
    def zw(c):                                         # 0x409150에 복사된 ntdll 스텁(stdcall 5인자)
        cls, buf = c.arg(2), c.arg(3)
        if cls == 7: c.uc.mem_write(buf, b'\0\0\0\0'); c.ret(0, 0x14)
        elif cls == 0x1e: c.uc.mem_write(buf, b'\0\0\0\0'); c.ret(0xc0000353, 0x14)
        elif cls == 0x1f: c.uc.mem_write(buf, b'\1\0\0\0'); c.ret(0, 0x14)
        else: c.log.append(f'UNKNOWN ZW CLASS {cls:#x}'); c.ret(0xc0000001, 0x14)
    ctx.stubs[0x409150] = zw
def handle_exception(ctx, pc):                         # 필터 0x401140: [ctx+0xb8] += 2, EXCEPTION_CONTINUE_EXECUTION
    ctx.uc.reg_write(UC_X86_REG_EIP, pc + 2)
    return True
