# Unicorn 기반 함수 단위 에뮬레이터(EMULATION.md의 예외 절차). 대상 코드는 격리된 메모리 모델 안에서만 돌고 OS 자원(syscall, 파일, 네트워크)에 닿지 않는다. 호출은 프로필(profiles/*.py)이 정한 스텁으로 대체된다.
# 사용: .REA/bin/python -I tools/emu/unicorn_run.py <gate.md> <pe> <profile.py> start=0x.. max=N [stop=0x..,..] [input=TEXT | input=search:N] [fill=C] [out=<trace 경로>]
#   input=search:N: 길이 N 입력을 앞 글자부터 확정한다. 각 위치마다 인쇄 가능 ASCII(0x20-0x7e)를 시도해 실행 단계 수(steps)가 가장 큰 글자를 고르고(동률이면 모두 보고), 나머지 자리는 fill(기본 A)로 채운다. 마지막에 확정 입력을 한 번 더 돌려 trace를 out에 쓴다.
# 승인: 에이전트가 사용자 승인(하네스 확인 창 또는 사용자 응답) 뒤에 gate.md 끝에 `승인: YYYY-MM-DD, 범위: <scope>`를 쓴다. 이 러너는 같은 범위 줄이 없으면 시행하지 않고 거부한다(스스로 줄을 쓰지 않는다). scope 문자열은 거부 메시지에 그대로 출력된다.
#   watch=0xADDR:LEN[,..]: 종료 시 그 메모리 구간을 16진으로 출력한다. 시작 시 PE 섹션 매핑을 파일 원본과 대조한다(MAPCHECK).
import sys, os, hashlib, importlib.util, datetime
import pefile
from unicorn import Uc, UcError, UC_ARCH_X86, UC_MODE_32, UC_HOOK_CODE, UC_HOOK_MEM_WRITE, UC_PROT_ALL
from unicorn.x86_const import *

gate, pe_path, prof_path = sys.argv[1:4]
kv = dict(a.split('=', 1) for a in sys.argv[4:])
start = int(kv['start'], 0); max_steps = int(kv['max']); stops = {int(x, 0) for x in kv.get('stop', '').split(',') if x}
text = kv.get('input', ''); out = kv.get('out', 'analysis/emu-trace.txt'); fill = kv.get('fill', 'A')
watch = [(int(a, 0), int(b, 0)) for a, b in (w.split(':') for w in kv.get('watch', '').split(',') if w)]
sha = hashlib.sha256(open(pe_path, 'rb').read()).hexdigest()[:12]
scope = f'pe={sha} start={start:#x} input={text!r} fill={fill!r} stop={sorted(map(hex, stops))} max={max_steps}'
if not any(l.startswith('승인:') and scope in l for l in open(gate, encoding='utf-8').read().splitlines()):
    sys.exit(f'REFUSED: {gate}에 이 범위의 `승인:` 줄이 없다. 사용자 승인 뒤 아래를 추가:\n승인: {datetime.date.today()}, 범위: {scope}')

pe = pefile.PE(pe_path)
base = pe.OPTIONAL_HEADER.ImageBase
size = (pe.OPTIONAL_HEADER.SizeOfImage + 0xfff) & ~0xfff
raw = open(pe_path, 'rb').read()
image = [(0, pe.header)] + [(s.VirtualAddress, s.get_data()) for s in pe.sections]
for s_ in pe.sections:  # MAPCHECK: 매핑에 쓸 섹션 데이터가 파일의 PointerToRawData 구간과 같은지 대조
    n_ = min(s_.SizeOfRawData, s_.Misc_VirtualSize)
    assert s_.get_data()[:n_] == raw[s_.PointerToRawData:s_.PointerToRawData + n_], f'MAPCHECK FAIL {s_.Name!r}'
print('MAPCHECK ok', [s_.Name.rstrip(b'\0').decode() for s_ in pe.sections])
spec = importlib.util.spec_from_file_location('profile', prof_path)
prof = importlib.util.module_from_spec(spec); spec.loader.exec_module(prof)
STACK, STACK_SZ, SENTINEL = 0x00200000, 0x100000, 0xDEAD0000
code_lo, code_hi = base + 0x1000, base + 0x8000

class Ctx:
    pass

def run_one(inp):
    uc = Uc(UC_ARCH_X86, UC_MODE_32)
    uc.mem_map(base, size + 0x10000, UC_PROT_ALL)
    for va, data in image:
        uc.mem_write(base + va, data)
    uc.mem_map(STACK, STACK_SZ, UC_PROT_ALL)
    ctx = Ctx(); ctx.uc = uc; ctx.text = inp; ctx.stubs = {}; ctx.log = []; ctx.base = base
    def arg(n):  # 호출 직후 [esp+4*n] (n=0은 반환 주소)
        return int.from_bytes(uc.mem_read(uc.reg_read(UC_X86_REG_ESP) + 4 * n, 4), 'little')
    def cstr(a):
        b = bytearray()
        while len(b) <= 200:
            c = uc.mem_read(a, 1)[0]
            if c == 0: break
            b.append(c); a += 1
        return bytes(b).decode('latin1')
    def ret(eax, pop=0):  # 스텁 반환: eax 설정, 반환 주소를 꺼내고 인자 pop 바이트 정리
        esp = uc.reg_read(UC_X86_REG_ESP)
        r = int.from_bytes(uc.mem_read(esp, 4), 'little')
        uc.reg_write(UC_X86_REG_EAX, eax & 0xffffffff)
        uc.reg_write(UC_X86_REG_ESP, esp + 4 + pop)
        uc.reg_write(UC_X86_REG_EIP, r)
    ctx.arg, ctx.cstr, ctx.ret = arg, cstr, ret
    prof.setup(ctx)
    esp = STACK + STACK_SZ - 0x1000
    uc.mem_write(esp - 4, SENTINEL.to_bytes(4, 'little'))
    uc.reg_write(UC_X86_REG_ESP, esp - 4); uc.reg_write(UC_X86_REG_EBP, esp - 4)
    steps = [0]; trace = []; writes = []
    def on_code(u, addr, sz, _):
        steps[0] += 1
        if addr in ctx.stubs:
            ctx.stubs[addr](ctx); return
        if addr in stops or addr == SENTINEL or steps[0] >= max_steps:
            u.emu_stop(); return
        trace.append((addr, bytes(u.mem_read(addr, 15))))
    def on_write(u, access, addr, sz, val, _):
        if code_lo <= addr < code_hi:
            writes.append((steps[0], addr, sz, val & ((1 << (8 * sz)) - 1)))
    uc.hook_add(UC_HOOK_CODE, on_code)
    uc.hook_add(UC_HOOK_MEM_WRITE, on_write)
    pc = start; exc = 0
    uc.reg_write(UC_X86_REG_EIP, start)
    while True:
        try:
            uc.emu_start(pc, 0xFFFFFFFF)
            pc = uc.reg_read(UC_X86_REG_EIP)
            status = f'STOP@{pc:#x}' if (pc in stops or pc == SENTINEL) else ('CAP' if steps[0] >= max_steps else f'HALT@{pc:#x}')
            break
        except UcError as e:
            pc = uc.reg_read(UC_X86_REG_EIP); exc += 1
            ctx.log.append(f'EXC#{exc}@{pc:#x} {e} (필터 0x401140과 같게 EIP+2로 계속)')
            if exc > 200 or not prof.handle_exception(ctx, pc):
                status = f'FAULT@{pc:#x} {e}'; break
            pc = uc.reg_read(UC_X86_REG_EIP)
    ctx.watch = [(a, bytes(uc.mem_read(a, n)).hex()) for a, n in watch]
    return status, steps[0], trace, writes, exc, ctx

def dump(inp, res, path):
    status, nsteps, trace, writes, exc, ctx = res
    os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
    with open(path, 'w') as f:
        f.write(f'# {scope}\n# input={inp!r} status={status} steps={nsteps}\n')
        for i, (a, b) in enumerate(trace): f.write(f'{i}\t{a:#x}\t{b.hex()}\n')
        f.write('# CODE WRITES (step addr size value)\n')
        for w in writes: f.write(f'W\t{w[0]}\t{w[1]:#x}\t{w[2]}\t{w[3]:#x}\n')
        for l in ctx.log: f.write(f'# {l}\n')

if text.startswith('sweep:'):  # sweep:<기준 입력>: 각 위치를 인쇄 가능 ASCII 95종으로 바꿔 stop 주소 중 첫 번째(Correct)에 도달하는 글자를 위치별로 보고(유일성 점검)
    base_in = text.split(':', 1)[1]; ok_stop = f'STOP@{sorted(stops)[0]:#x}'
    for pos in range(len(base_in)):
        good = ''
        for c in range(0x20, 0x7f):
            cand = list(base_in); cand[pos] = chr(c)
            if run_one(''.join(cand))[0] == ok_stop: good += chr(c)
        print(f'SWEEP POS {pos}: accepted={good!r}')
elif text.startswith('search:'):
    n = int(text.split(':')[1]); cur = list(fill * n); fixed = [False] * n
    for rnd in range(12):  # 비교가 순차라서 앞 글자가 맞아야 다음 글자의 비교가 실행된다: 확정이 안 늘 때까지 반복
        changed = False
        for pos in range(n):
            if fixed[pos]: continue
            scores = {}
            for c in range(0x20, 0x7f):
                cand = cur[:]; cand[pos] = chr(c)
                r = run_one(''.join(cand))
                scores[chr(c)] = r[1]
            best = max(scores.values()); top = [c for c, v in scores.items() if v == best]
            if len(top) == 1 and best > min(scores.values()):
                cur[pos] = top[0]; fixed[pos] = True; changed = True
                print(f'ROUND {rnd} POS {pos}: {top[0]!r} steps={best} (min {min(scores.values())})')
        if not changed or all(fixed): break
    print('UNFIXED', [i for i in range(n) if not fixed[i]])
    final = ''.join(cur)
    res = run_one(final); dump(final, res, out)
    print(f'FINAL input={final!r} status={res[0]} steps={res[1]} exceptions={res[4]}')
else:
    res = run_one(text); dump(text, res, out)
    for a, h in res[5].watch: print(f'WATCH {a:#x}: {h}')
    print(f'EMU start={start:#x} input={text!r} status={res[0]} steps={res[1]} traced={len(res[2])} code_writes={len(res[3])} exceptions={res[4]}')
    for l in res[5].log[:8]: print('LOG', l)
print('TRACE', out)
