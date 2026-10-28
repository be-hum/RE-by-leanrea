#!/usr/bin/env bash
# Usage: tools/ghidra/analyze.sh targets/<name>/<binary>
# Project DB -> analysis/<name>/ghidra, exports -> analysis/<name>/<binary>/
set -euo pipefail
bin=$(realpath "$1")
root=$(cd "$(dirname "$0")/../.." && pwd)
name=$(basename "$(dirname "$bin")")
out="$root/analysis/$name/$(basename "$bin")"
mkdir -p "$root/analysis/$name/ghidra" "$out"
"${GHIDRA_HOME:-$HOME/tools/ghidra}/support/analyzeHeadless" \
  "$root/analysis/$name/ghidra" "$name" -import "$bin" -overwrite \
  -scriptPath "$root/tools/ghidra" -postScript ExportAll.java "$out" \
  2>&1 | tee "$out/headless.log" | grep -E 'ExportAll|ERROR|Import succeeded' || true
