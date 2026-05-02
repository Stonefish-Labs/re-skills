#!/usr/bin/env sh
set -eu
clang -arch arm64 -Wl,-e,_start -Wl,-dead_strip exit_dynamic.s -o tiny_exit
clang -arch arm64 -Wl,-e,_start -Wl,-dead_strip write_dynamic.s -o tiny_write
