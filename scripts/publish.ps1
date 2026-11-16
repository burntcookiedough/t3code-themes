# Regenerate the Soft Bloom theme and install it into T3 Code.
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
# Use `t3` if it's on PATH, otherwise T3 Code's default install location.
$t3 = if (Get-Command t3 -ErrorAction SilentlyContinue) { "t3" } else { Join-Path $HOME ".t3\bin\t3.cmd" }
python "$root/src/generate.py" "$root/themes/soft-bloom.json"
& $t3 theme set "$root/themes/soft-bloom.json"
