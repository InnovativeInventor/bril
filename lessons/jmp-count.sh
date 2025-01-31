#!/usr/bin/env bash
# Counts the number of jump instructions using `jq` and `wc`.
jq '.functions[].instrs[] | select(.op == "jmp") | .op' | wc -l
