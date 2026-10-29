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
# Keyed on content, not file name: a re-unpacked binary with the same name must not reuse the stale DB.
sha=$(sha256sum "$bin" | cut -d' ' -f1)
stamp="$proj/.sha256-$(basename "$bin")"
if [[ "$(cat "$stamp" 2>/dev/null)" != "$sha" ]]; then
  echo "importing + analyzing $(basename "$bin") (on first use or content change, may take minutes)..." >&2
  run "$proj" "$name" -import "$bin" -overwrite -scriptPath "$root/tools/ghidra" -postScript FixEntry.java > "$out/import.log" 2>&1 \
    || { tail -20 "$out/import.log"; exit 1; }
  echo "$sha" > "$stamp"
fi

res="$out/query-$(date +%Y%m%d-%H%M%S)-$$.txt"
run "$proj" "$name" -process "$(basename "$bin")" -noanalysis -readOnly \
  -scriptPath "$root/tools/ghidra" -postScript Query.java "$res" "$@" > "$out/query-$$.log" 2>&1 \
  || { tail -20 "$out/query-$$.log"; exit 1; }
rm -f "$out/query-$$.log"

# Breadcrumb: one row per resolved function, so the explored call path survives across calls.
# Recall with: column -t -s $'\t' analysis/<name>/trail.tsv
awk -v ts="$(date +%F' '%T)" -v bin="$(basename "$bin")" -v full="$(basename "$res")" '
  function flush() { gsub(/<EXTERNAL>::/, "", ce); if (fn != "") print ts "\t" bin "\t" q "\t" fn "\t" substr(cr, 2) "\t" substr(ce, 2) "\t" full; fn = "" }
  /^==== QUERY / {
    flush(); s = substr($0, 12); i = index(s, " -> "); q = substr(s, 1, i - 1); s = substr(s, i + 4)
    j = match(s, / @ [^ ]+$/); fn = substr(s, 1, j - 1) "@" substr(s, j + 3); cr = ce = ""
  }
  /^CALLER / { cr = cr "," $3 }
  /^CALLEE / { ce = ce "," $3 }
  END { flush() }
' "$res" >> "$root/analysis/$name/trail.tsv"

# Past QUERY_MAX_LINES, print a skeleton of the rest (control flow, labels, call statements) with
# line numbers into the full file, so a specific block can be read with sed -n '<from>,<to>p'.
awk -v max="${QUERY_MAX_LINES:-200}" -v skmax="${QUERY_SKEL_LINES:-100}" -v full="$res" '
  /^==== QUERY/ { n = 0; cut = 0; sk = 0 }
  /^[[:space:]]*\/\* WARNING:.*\*\/[[:space:]]*$/ || /^[[:space:]]*$/ { next }
  ++n <= max { print; next }
  !cut { print "// ... truncated at " max " lines, skeleton of the rest follows (L<n> = line in " full ")"; cut = 1 }
  /^[[:space:]]*(}[[:space:]]*)?(if|while|for|switch)[[:space:]]*\(|^[[:space:]]*(}[[:space:]]*)?(else|do)([[:space:]{]|$)|^[[:space:]]*(case .*|default):|^[[:space:]]*(return|goto)[[:space:](;]|^[[:space:]]*LAB_[0-9a-fA-F]+:|^[[:space:]]*([A-Za-z_][][A-Za-z0-9_.>-]*[[:space:]]*=[[:space:]]*)?(\([^()]*\)[[:space:]]*)?[A-Za-z_][A-Za-z0-9_]*\(/ {
    if (++sk <= skmax) printf "L%d: %s\n", NR, $0
    else if (sk == skmax + 1) print "// ... skeleton capped at " skmax " lines"
  }
' "$res"
