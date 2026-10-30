# 원래 위치: tmp/<name>/ (재사용을 위해 tools/scripts로 이동).
# 목적: objdump 출력의 구간에서 .rodata 범위 즉시값/lea 주소를 문자열로 주석해 출력. 사용: strann.py <elf> <objdump.txt> <시작주소hex> <끝주소hex>
import sys,re
elf,dis,a,b=sys.argv[1],sys.argv[2],int(sys.argv[3],16),int(sys.argv[4],16)
data=open(elf,'rb').read()
RO0,RO1,OFF=0x10001a0,0x100ac80,0  # .rodata VA==file offset (LOAD 0x0->0x1000000)
def cstr(va):
    o=va-0x1000000
    e=data.find(b'\0',o,o+120)
    s=data[o:e if e>0 else o+60]
    try:return s.decode('latin1').replace('\n','\\n')
    except:return ''
for l in open(dis):
    m=re.match(r'\s+([0-9a-f]+):\t(.*)',l)
    if not m:continue
    x=int(m.group(1),16)
    if not(a<=x<=b):continue
    ins=m.group(2).rstrip()
    t=re.search(r'\b0x(10[0-9a-f]{5})\b',ins)
    ann=''
    if t:
        v=int(t.group(1),16)
        if RO0<=v<RO1 and ('call' not in ins and not ins.startswith('j')):
            ann='   ; "'+cstr(v)+'"'
    print(f'{x:x}: {ins}{ann}')
