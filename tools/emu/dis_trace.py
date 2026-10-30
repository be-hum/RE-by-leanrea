# unicorn_run.py가 쓴 trace(번호, 주소, 15바이트)를 rasm2로 한 줄씩 디스어셈블해 출력한다. 사용: dis_trace.py <trace> [from] [count]. 대상 실행 없음.
import sys, subprocess
rows = [l.rstrip('\n').split('\t') for l in open(sys.argv[1]) if l[0].isdigit()]
a = int(sys.argv[2]) if len(sys.argv) > 2 else 0
n = int(sys.argv[3]) if len(sys.argv) > 3 else 60
for r in rows[a:a + n]:
    h = r[2]
    o = subprocess.run(['rasm2', '-a', 'x86', '-b', '32', '-d', h], capture_output=True, text=True).stdout.split('\n')[0]
    print(r[0], r[1], o)
