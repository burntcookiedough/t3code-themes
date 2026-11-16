#!/usr/bin/env sh
# Regenerate the Soft Bloom theme and install it into T3 Code.
set -e
root="$(cd "$(dirname "$0")/.." && pwd)"
python "$root/src/generate.py" "$root/themes/soft-bloom.json"
t3 theme set "$root/themes/soft-bloom.json"
