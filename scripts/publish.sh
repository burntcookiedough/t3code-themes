#!/usr/bin/env sh
# Regenerate the Soft Bloom theme and install it into T3 Code.
set -e
root="$(cd "$(dirname "$0")/.." && pwd)"
# Use `t3` if it's on PATH, otherwise T3 Code's default install location.
if command -v t3 >/dev/null 2>&1; then T3=t3; else T3="$HOME/.t3/bin/t3.cmd"; fi
python "$root/src/generate.py" "$root/themes/soft-bloom.json"
"$T3" theme set "$root/themes/soft-bloom.json"
