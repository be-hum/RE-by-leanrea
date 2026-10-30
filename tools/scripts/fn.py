# 원래 위치: tmp/<name>/ (재사용을 위해 tools/scripts로 이동).
# 목적: objdump 출력에서 call 대상 집합으로 함수 시작 주소를 추정하고, 구간을 .rodata 문자열 주석과 함께 출력. 사용: fn.py <elf> <objdump.txt> <rodata_lo hex> <rodata_hi hex> {start|dump} <addr hex> [끝 hex]
import sys,re,bisect
elf,dis,lo,hi,mode,a=sys.argv[1],sys.argv[2],int(sys.argv[3],16),int(sys.argv[4],16),sys.argv[5],int(sys.argv[6],16)
data=open(elf,'rb').read()
lines=[];targets=set()
for l in open(dis):
    m=re.match(r'\s+([0-9a-f]+):\t(.*)',l)
    if not m:continue
    x=int(m.group(1),16);ins=m.group(2).rstrip();lines.append((x,ins))
    t=re.match(r'call\s+0x([0-9a-f]+)',ins)
    if t:targets.add(int(t.group(1),16))
ts=sorted(targets)
def fstart(x):
    i=bisect.bisect_right(ts,x)-1
    return ts[i] if i>=0 else None
def s(v):
    b=data[v:v+70];out=''
    for c in b:
        out+=chr(c) if 32<=c<127 else '.'
    return out
if mode=='start':
    print(hex(fstart(a)));sys.exit()
b=int(sys.argv[7],16) if len(sys.argv)>7 else None
st=fstart(a) if b is None else a
en=b if b else None
for x,ins in lines:
    if x<st:continue
    if en and x>en:break
    if not en and x>st and x in targets:break
    ann=''
    t=re.search(r'# 0x([0-9a-f]+)',ins)
    if t:
        v=int(t.group(1),16)
        if lo<=v<hi and 'call' not in ins:ann='   ; "'+s(v)+'"'
    print(f'{x:x}: {ins}{ann}')
