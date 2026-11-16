# Regenerate the Soft Bloom theme and install it into T3 Code.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
python "$root/src/generate.py" "$root/themes/soft-bloom.json"
t3 theme set "$root/themes/soft-bloom.json"
