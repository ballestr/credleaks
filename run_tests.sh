#!/bin/bash
models=(
    "qwen3:8b"
    "qwen2.5-coder:7b"
    "qwen2.5-coder:1.5b"
    "llama3.2:latest"
    "deepseek-r1:7b"
)
for m in ${models[@]}; do
    name=${m//:/_}
    ./credleaks --model=$m tests/ | tee test_${name}.log
done
