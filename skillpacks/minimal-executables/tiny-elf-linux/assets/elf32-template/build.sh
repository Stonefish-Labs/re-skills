#!/usr/bin/env sh
set -eu
script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
generator="$script_dir/../../scripts/make_tiny_elf.py"
python3 "$generator" --arch i386 --behavior exit --tier conservative --output tiny_exit32
python3 "$generator" --arch i386 --behavior write --tier aggressive --output tiny_write32
