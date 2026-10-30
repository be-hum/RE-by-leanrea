# 목적: stripped Rust ELF64(x86-64, static-pie/PIE)에서 패닉 Location{ptr,len,line,col}을 복원해 소스 경로·줄·열 표를 출력(METHODS M-301, M-008 앵커).
# 방법: .rela.dyn의 R_X86_64_RELATIVE 중 r_offset이 .data.rel.ro 안이고 addend가 `.rs`로 끝나는 문자열을 가리키는 것을 Location으로 본다(+8 len, +16 line u32, +20 col u32).
# 사용: rust_locs.py <elf> [경로 부분문자열] [objdump.txt]  -> TSV: loc_va  path  line  col  [refs: Location을 `# 0x..`로 참조하는 명령 주소]
# 생성: notes/ripgrep/05-reanalysis.md, notes/zoxide/01-overview.md의 일회성 스캔을 재사용용으로 다시 작성(2026-10-30).
import sys,struct,re
elf=open(sys.argv[1],'rb').read()
want=sys.argv[2] if len(sys.argv)>2 else ''
assert elf[:4]==b'\x7fELF' and elf[4]==2, 'ELF64 only'
shoff,=struct.unpack_from('<Q',elf,0x28);shentsz,shnum,shstrndx=struct.unpack_from('<HHH',elf,0x3a)
phoff,=struct.unpack_from('<Q',elf,0x20);phentsz,phnum=struct.unpack_from('<HH',elf,0x36)
S=[struct.unpack_from('<IIQQQQIIQQ',elf,shoff+i*shentsz) for i in range(shnum)]
strtab=S[shstrndx][4]
def sname(s): o=strtab+s[0]; return elf[o:elf.index(b'\0',o)].decode()
sec={sname(s):s for s in S}
loads=[p for p in (struct.unpack_from('<IIQQQQQQ',elf,phoff+i*phentsz) for i in range(phnum)) if p[0]==1]
def off(va):
    for p in loads:
        if p[3]<=va<p[3]+p[5]: return va-p[3]+p[2]
rel,ro=sec['.rela.dyn'],sec['.data.rel.ro']
lo,hi=ro[3],ro[3]+ro[5]
locs=[]
for i in range(0,rel[5],24):
    r_off,info,add=struct.unpack_from('<QQq',elf,rel[4]+i)
    if info&0xffffffff!=8 or not lo<=r_off<hi-24: continue
    o,so=off(r_off),off(add)
    if o is None or so is None: continue
    n,line,col=struct.unpack_from('<QII',elf,o+8)
    if not 3<n<512: continue
    p=elf[so:so+n]
    if not p.endswith(b'.rs'): continue
    p=p.decode('utf-8','replace')
    if want in p: locs.append((r_off,p,line,col))
refs={}
if len(sys.argv)>3:
    keys={f'{v:x}' for v,*_ in locs}
    for l in open(sys.argv[3]):
        m=re.match(r'\s+([0-9a-f]+):.*#\s*0x([0-9a-f]+)',l)
        if m and m.group(2) in keys: refs.setdefault(int(m.group(2),16),[]).append('0x'+m.group(1))
for v,p,line,col in sorted(locs,key=lambda x:(x[1],x[2],x[3])):
    print(f'{v:#x}\t{p}\t{line}\t{col}'+(f"\t{','.join(refs[v])}" if v in refs else ''))
