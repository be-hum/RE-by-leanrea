#!/usr/bin/env bash
# Usage: tools/ghidra/query.sh targets/<name>/<binary> <func|0xaddr|str:text>...
# First call imports + auto-analyzes into analysis/<name>/ghidra (once); later calls reuse it read-only.
# Result is printed and saved to analysis/<name>/<binary>/query-<timestamp>.txt
set -euo pipefail
bin=$(realpath "$1"); shift
root=$(cd "$(dirname "$0")/../.." && pwd)
name=$(basename "$(dirname "$bin")")
proj="$root/analysis/$name/ghidra"
out="$root/analysis/$name/$(basename "$bin")"
headless="${GHIDRA_HOME:-$HOME/tools/ghidra}/support/analyzeHeadless"
mkdir -p "$proj" "$out"
if [[ ! -e "$proj/$name.rep/idata/~index.dat" ]] || ! grep -q "$(basename "$bin")" "$proj/$name.rep/idata/~index.dat"; then
  "$headless" "$proj" "$name" -import "$bin" > "$out/import.log" 2>&1 \
    || { tail -20 "$out/import.log"; exit 1; }
fi
res="$out/query-$(date +%Y%m%d-%H%M%S).txt"
"$headless" "$proj" "$name" -process "$(basename "$bin")" -noanalysis -readOnly \
  -scriptPath "$root/tools/ghidra" -postScript Query.java "$res" "$@" > "$out/query.log" 2>&1 \
  || { tail -20 "$out/query.log"; exit 1; }
cat "$res"
