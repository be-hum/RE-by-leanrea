#!/usr/bin/env bash
# Usage: tools/ghidra/query.sh targets/<name>/<binary> <func|0xaddr|str:text>...
# First call imports + auto-analyzes into analysis/<name>/ghidra (once, minutes); later calls reuse it read-only.
# Each call costs ~5s JVM startup: batch all points of a round into one call.
# Full result is saved to analysis/<name>/<binary>/query-*.txt; stdout is a trimmed view
# (Ghidra WARNING comments and blank lines dropped, each function capped at QUERY_MAX_LINES, default 200).
set -euo pipefail
bin=$(realpath "$1"); shift
root=$(cd "$(dirname "$0")/../.." && pwd)
name=$(basename "$(dirname "$bin")")
proj="$root/analysis/$name/ghidra"
out="$root/analysis/$name/$(basename "$bin")"
headless="${GHIDRA_HOME:-$HOME/tools/ghidra}/support/analyzeHeadless"
mkdir -p "$proj" "$out"
# analyzeHeadless runs the JVM as a child; don't leave it orphaned if this wrapper is interrupted.
trap 'kill $(jobs -p) 2>/dev/null' INT TERM HUP

run() { "$headless" "$@" & wait $!; }

# Ghidra locks the project exclusively (even -readOnly): queue concurrent calls on the same target instead of failing.
exec 9>"$proj/.flock"
flock 9
if [[ ! -e "$proj/$name.rep/idata/~index.dat" ]] || ! grep -q "$(basename "$bin")" "$proj/$name.rep/idata/~index.dat"; then
  echo "importing + analyzing $(basename "$bin") (one-time, may take minutes)..." >&2
  run "$proj" "$name" -import "$bin" -scriptPath "$root/tools/ghidra" -postScript FixEntry.java > "$out/import.log" 2>&1 \
    || { tail -20 "$out/import.log"; exit 1; }
fi

res="$out/query-$(date +%Y%m%d-%H%M%S)-$$.txt"
run "$proj" "$name" -process "$(basename "$bin")" -noanalysis -readOnly \
  -scriptPath "$root/tools/ghidra" -postScript Query.java "$res" "$@" > "$out/query-$$.log" 2>&1 \
  || { tail -20 "$out/query-$$.log"; exit 1; }
rm -f "$out/query-$$.log"

awk -v max="${QUERY_MAX_LINES:-200}" -v full="$res" '
  /^==== QUERY/ { n = 0; cut = 0 }
  /^[[:space:]]*\/\* WARNING:.*\*\/[[:space:]]*$/ || /^[[:space:]]*$/ { next }
  { if (++n <= max) print; else if (!cut) { print "// ... truncated at " max " lines, full output: " full; cut = 1 } }
' "$res"
