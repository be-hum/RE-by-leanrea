// 원래 위치: tmp/<name>/gofuncs (age, restic에서 사용). 분석 완료 후 tmp 삭제 규칙 때문에 재사용 스크립트만 tools/scripts로 옮김.
// 목적: stripped Go 바이너리의 pclntab을 debug/gosym으로 읽어 함수 표(entry, end, name)를 출력. PIE는 .data.rel.ro에서 매직 탐색.
package main

import (
	"debug/elf"
	"debug/gosym"
	"fmt"
	"os"
)

func main() {
	f, err := elf.Open(os.Args[1])
	if err != nil {
		panic(err)
	}
	text := f.Section(".text")
	var data []byte
	if pcln := f.Section(".gopclntab"); pcln != nil {
		data, err = pcln.Data()
	} else {
		// PIE: pclntab lives inside .data.rel.ro; locate go1.20+ magic
		ro := f.Section(".data.rel.ro")
		all, _ := ro.Data()
		for i := 0; i+8 < len(all); i += 8 {
			if all[i] == 0xf1 && all[i+1] == 0xff && all[i+2] == 0xff && all[i+3] == 0xff && all[i+4] == 0 && all[i+5] == 0 {
				data = all[i:]
				fmt.Fprintf(os.Stderr, "pclntab at %#x\n", ro.Addr+uint64(i))
				break
			}
		}
	}
	if data == nil {
		panic("pclntab not found")
	}
	t, err := gosym.NewTable(nil, gosym.NewLineTable(data, text.Addr))
	if err != nil {
		panic(err)
	}
	for _, fn := range t.Funcs {
		fmt.Printf("%x\t%x\t%s\n", fn.Entry, fn.End, fn.Name)
	}
}
