#!/usr/bin/env bash
# Every gate this project has, in the order a failure is cheapest to diagnose.
# Run it before showing anything: a green result on a stale build has wasted
# more rounds here than any drawing fault.
set -uo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."
fail=0
run() {
    printf '\n=== %s ===\n' "$1"; shift
    if ! "$@"; then fail=1; fi
}
run "mechanical + interpolation" ./venv/bin/python tools/check.py
run "audit: drawn glyphs"        ./venv/bin/python tools/audit.py
run "audit: the face's own Latin (thresholds must not flag it)" \
    ./venv/bin/python tools/audit.py --selftest
run "panel: ink area"            ./venv/bin/python tools/panel.py
run "panel: stroke weight"       ./venv/bin/python tools/strokes.py
run "signature: the face's own Latin (both readings must not flag it)" \
    ./venv/bin/python tools/signature.py --selftest
run "signature: drawn glyphs"    ./venv/bin/python tools/signature.py
printf '\n'
if [ "$fail" -ne 0 ]; then echo "SOMETHING FAILED"; exit 1; fi
echo "all gates pass"
