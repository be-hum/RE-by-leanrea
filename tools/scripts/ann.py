# 원래 위치: tmp/<name>/ (재사용을 위해 tools/scripts로 이동).
# 목적: 함수 표(tsv)로 objdump 출력의 call 대상에 함수명을 주석하고 지정 함수 구간만 출력.
import sys,re,bisect
F=[(int(a,16),int(b,16),n) for a,b,n in (l.rstrip('\n').split('\t') for l in open(sys.argv[1]) if not l.startswith('#'))]
F.sort();starts=[f[0] for f in F]
def name(x):
    i=bisect.bisect_right(starts,x)-1
    if i>=0 and F[i][0]<=x<F[i][1]: return F[i][2]+('' if x==F[i][0] else f'+{x-F[i][0]:#x}')
want=sys.argv[3:]
rng=[(a,b,n) for a,b,n in F if n in want]
lines=open(sys.argv[2]).read().splitlines()
for a,b,n in rng:
    print(f'==== {n} {a:#x}-{b:#x}')
    for l in lines:
        m=re.match(r'\s+([0-9a-f]+):\t(.*)',l)
        if not m:continue
        x=int(m.group(1),16)
        if a<=x<b:
            ins=m.group(2)
            t=re.search(r'(call|j\w+)\s+(?:0x)?([0-9a-f]+)',ins)
            if t and t.group(1)=='call':ins+='   ; '+str(name(int(t.group(2),16)))
            r=re.search(r'\[rip\+0x[0-9a-f]+\]\s+# ([0-9a-f]+)',ins)
            print(f'{x:x}: {ins}')
