---
name: leanrea
description: Reverse engineer shipped software with plain local CLI tools on WSL2/Linux, no MCP needed. Covers Electron/JS bundles, native ELF/PE/Mach-O, Go/Rust/.NET/Flutter/WASM binaries, APKs, SQLite, pcaps, firmware and websites, including Windows apps under /mnt/c. Use to explain how a feature works, extract versions/deps, compare builds, or rebuild a feature.
---

# leanrea: fast path (WSL2 / Linux)

You already know these tools. This file only lists the fastest command for each target, and the traps. `T` is the target copy and `$D` the per-target work dir. Methods learned from real analyses (what failed first and what fixed it) live in `METHODS.md` next to this file: check it when a Router row's tool fails or a result looks wrong.

## First move: one call each, paste and run
Native (ELF):
```sh
T=./bin; D=<workdir>; mkdir -p $D; file $T; echo '--- HDR'; readelf -hW $T | rg 'Class|Machine|Type'; echo '--- NEEDED'; readelf -dW $T | rg 'NEEDED|RUNPATH|RPATH'; echo '--- EXPORTS'; nm -DC --defined-only $T | head -150; echo '--- IMPORTS'; nm -DuC $T | awk '{print $NF}' | tr '\n' ' '; echo; echo '--- STRINGS'; strings -a -n 6 $T | rg -v '^[_$.]' | head -400; objdump -dC --no-show-raw-insn -M intel $T > $D/dis.txt; echo '--- FUNCS'; rg -o '^[0-9a-f]+ <[^>]+>:$' $D/dis.txt | head -150
```
Then read one function: `awk '/<FUNC>:$/{p=1;next} p&&/^[0-9a-f]+ <.*>:$/{exit} p' $D/dis.txt | rg 'call|j[a-z]+ |cmp|lea.*rip'`.

Windows PE (from `/mnt/c`):
```sh
T=./app.exe; file $T; objdump -x $T | rg -A40 'DLL Name|Export Address' | head -150; strings -a -n 6 $T | head -300; strings -a -el -n 6 $T | head -200
```
`strings -el` catches UTF-16 strings, which most Windows apps use. Resources: `7z x -o$D/rsrc $T` extracts `.rsrc` (manifest, version info, icons).

Electron (Windows install is usually `/mnt/c/Users/<u>/AppData/Local/Programs/<App>/resources/app.asar`):
```sh
A=./app.asar; X=$D/asar; rm -rf $X; npx -y @electron/asar extract $A $X && jq '{name,version,main}' $X/package.json; find $X -path '*/node_modules' -prune -o -type f \( -name '*.js' -o -name '*.node' \) -print | head -60; ls ${A}.unpacked/node_modules 2>/dev/null; rg -uu -l --glob '!node_modules' 'exposeInMainWorld' $X
```
Then slice the needle across the bundle: `rg -uu -o --glob '!node_modules' '.{0,250}NEEDLE.{0,250}' $X | head -20`.

Go: `go version -m T` alone usually answers the question (works on ELF, PE and Mach-O).

## Router
| Target (detect) | Fastest path |
|---|---|
| Electron app (`resources/app.asar`) | `npx -y @electron/asar extract app.asar X` (also see `app.asar.unpacked/` for `.node` addons). Entry: `jq .main X/package.json`. Surface: `rg -n -o '.{0,120}(ipcMain\.(handle\|handleOnce\|on\|once)\|ipcRenderer\.(invoke\|send\|sendSync\|on)\|contextBridge\.exposeIn(Main\|Isolated)World\|webPreferences\|preload:\|nodeIntegration\|contextIsolation\|sandbox\|\.node\b).{0,160}' -uu X --glob '!node_modules'`. Hidden channels: `rg -uu -o '"[a-z]+:[a-z0-9:-]+"' X/<main> \| sort -u`. Fuses: `npx -y @electron/fuses read --app <path to .exe>`. |
| Web bundle / minified JS | Find `sourceMappingURL`. If the map has `sourcesContent`, dump the sources: `jq -r '.sources[]'`. For webpack, grep the module ids, then slice around the hit. Pretty-print: `npx -y prettier --parser babel F > F.pretty.js`, then read with line ranges. |
| Hermes / bytenode / V8 snapshot | Hermes magic is `c6 1f bc 03` (`index.android.bundle`): `hbc-decompiler` (hermes-dec). `.jsc` (bytenode) cannot be decompiled: use strings and runtime hooks. |
| ELF (`file`: ELF) | `readelf -hlSW`, `readelf -dW` (NEEDED/RUNPATH), `nm -DC --defined-only` (exports), `nm -DuC` (imports = capability map), `strings -a -n 6`, `ldd T` (only on trusted binaries: it can execute code), `readelf -n` (build-id, ABI). Hardening without checksec: `readelf -lW T \| rg 'GNU_STACK\|GNU_RELRO'`, `readelf -dW T \| rg 'BIND_NOW\|FLAGS'`, `readelf -sW T \| rg -m1 __stack_chk_fail`, `file` says "pie executable". |
| PE (`file`: PE32/PE32+) | `objdump -x T` (imports per DLL, exports, sections), `strings -a -el` for UTF-16, `7z x` for `.rsrc`/installers (NSIS, Inno, MSI also open with `7z`). Disassembly: `objdump -d -M intel T`. Richer: `pefile` (`import pefile`). |
| Mach-O (`file`: Mach-O) | `r2 -qc 'iI;il;iE;ii' T` (info, libs, exports, imports); `strings -a -n 6`; fat binaries: `r2 -qc 'iA' T`. Or `llvm-objdump --macho -d` / `llvm-otool`. Entitlements/codesign: report as 미확인. |
| Native code logic | `objdump -dC --no-show-raw-insn -M intel T > $D/dis.txt`. Find the function: `rg -n '<.*Name.*>:$' $D/dis.txt`. Read the call/string trail: `rg 'call\|lea.*rip'` within it (objdump annotates `# addr <sym>`). String xref: find the string offset with `rg -boa 'X' T`, then `rg 'ADDR' $D/dis.txt`. Real pseudocode: `r2 -qc 'aaa; pdc @ sym.X' T` (or `afl~X` to find it first). |
| Go (`.go.buildinfo`) | `go version -m T`: toolchain, path, mod, deps, build flags. Symbols survive stripping: `go tool nm T \| rg ' main\.'`. |
| Rust | Deps (cargo-auditable): extract section `.dep-v0` with `objcopy -O binary --only-section=.dep-v0 T $D/dep.z` then `python3 -I -c 'import zlib,sys;print(zlib.decompress(open(sys.argv[1],"rb").read()).decode())' $D/dep.z \| jq`. Compiler: `strings -a T \| rg -o '/rustc/[0-9a-f]{40}' \| sort -u`. Crates: `strings -a T \| rg -o '[a-z0-9_-]+-[0-9]+\.[0-9]+\.[0-9]+/src' \| sort -u`. |
| .NET (`file`: Mono/.Net assembly) | `ilspycmd -p -o X T.dll`. Without it: `strings -a -el T` + `strings -a T \| rg 'DllImport\|\.dll'` for P/Invoke. NativeAOT/IL2CPP are native: use the PE/ELF rows. |
| Android APK | `unzip -l a.apk` for a quick look; `unzip -o a.apk -d $D/apk`. Manifest is binary XML: `jadx` or `apktool d`. `lib/*/libflutter.so` = Flutter (Dart AOT: `blutter`); `libhermes.so` = React Native (Hermes row). |
| Flutter snapshot hash | In `libapp.so`, find magic `f5 f5 dc dc` (`rg -boa $'\xf5\xf5\xdc\xdc' libapp.so` or `r2 -qc '/x f5f5dcdc'`); the 32 hex chars at +20 are the snapshot hash. Map it to a Dart version. |
| WASM | `wasm-objdump -x`, `wasm2wat`, `wasm-decompile` (WABT). Without WABT: `r2 -qc 'iI;ii;iE' F` for imports/exports, `strings -a F`. |
| SQLite | `sqlite3` CLI, or Python: copy the db (plus `-wal`), then `python3 -I -c 'import sqlite3,sys;c=sqlite3.connect(f"file:{sys.argv[1]}?mode=ro",uri=True);[print(r[0]) for r in c.execute("select sql from sqlite_master")]' C`. Then `SELECT * FROM t LIMIT 20` the same way. |
| plist / nib / car | `python3 -I -c 'import plistlib,sys,pprint;pprint.pprint(plistlib.load(open(sys.argv[1],"rb")))' F` (handles binary plists). Info.plist: bundle id, URL schemes, privacy strings. `Assets.car`: 미확인 without macOS. |
| pcap / HAR | `tshark`. HAR: `jq -r '.log.entries[].request \| .method+" "+.url'`. Quick pcap look without tshark: `strings -a C \| rg -o 'Host: .*\|[a-z0-9.-]+\.(com\|net\|io\|org)' \| sort -u`. |
| Firmware | `binwalk -e -C $D/fw F`. Then route each extracted binary through this table. |
| Website | `curl -sL URL` for the HTML and script srcs, then fetch the JS and slice it. Runtime/network behavior: claude-in-chrome (`read_network_requests`, `javascript_tool`). |
| Running process | Linux: `strace -f -e trace=file,network -p PID`, `ltrace -p PID`, `gdb -p PID`, `ls -l /proc/PID/fd`, `cat /proc/PID/maps`. Windows processes are not visible from WSL: `powershell.exe -c 'Get-Process X \| fl *'` for basics only. Electron main: `--inspect` (only if the RunAsNode/inspect fuses allow it). |

## Speed patterns
- On a small binary, `nm -Du` + `strings` + the export list usually answer "what does it do" with no disassembly. On PE, the import table per DLL plays the same role.
- To find who uses a string: get its virtual address (`r2 -qc 'izz~X' T`), then `r2 -qc 'aaa; axt @ ADDR' T` lists the referencing functions.
- An imported name at a `call` site already tells you the protocol (for example `connect`, `getpeereid`, `CryptProtectData`). Read the call sequence, not every instruction.
- For JS, go from the native/JS boundary inward: find the native call, then its caller class, then the IPC registration, then the renderer/preload.
- Comparing versions: diff the inventories (`nm`, `objdump -x` imports, the module list, `go version -m`) before you diff any code.
- Rebuilding: write the minimal reimplementation, then check it against expected values taken statically from the original (embedded constants, comparison targets, known-good samples).
