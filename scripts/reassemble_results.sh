#!/usr/bin/env sh
set -eu
parts_dir="${1:-./results_bundle.zip.parts}"
output="${2:-./results_bundle.zip}"
expected="${3:-fd5539a688e9b69bcf1f543518f08e1bbd8818e928f1f2c991ee24260857e1c7}"
: > "$output"
for part in "$parts_dir"/results_bundle.zip.part*; do
  cat "$part" >> "$output"
done
actual=$(sha256sum "$output" | awk '{print $1}')
if [ "$actual" != "$expected" ]; then
  echo "SHA256 mismatch: $actual" >&2
  exit 1
fi
echo "Reassembled and verified: $output"
echo "SHA256: $actual"
