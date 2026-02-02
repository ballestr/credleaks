# Test files and results

## Test files

It's very important to avoid providing additional clues to the model in the test files. In particular, never write in the file whether there is a secret or not. The model should decide that on its own. The test files should be as realistic as possible.

### `unbound.conf`

This file contains a real configuration of the unbound DNS server. Some models may think that the filenames of the certificates are secrets. They are not. They are just filenames.

### `monit.conf.erb`

This contains an actual password, but it's not clearly identifiable as such. It's a good test for the model's ability to detect secrets in configuration files.

### `gitleaks.test`

This contains a list used for pattern matching by gitleaks. LLM models may think that these are not real passwords because they contain the word "test" in them. They are a good example of how LLM models can be tricked by the context.

## Setup

Tested on a MacBook Air M2 (2022) with 16GB of RAM. 
Ollama installed via Homebrew. Context set globally at 32k.

Models tested:
- qwen3:8b
- qwen2.5-coder:1.5b
- qwen2.5-coder:7b
- llama3.2:latest
- deepseek-r1:7b

Command line like:
```
$ ./credleaks --model=deepseek-r1:7b tests/
...
## Summary: scanned=3 files_with_issues=2 total_issues=8 errors=0 total_time=0:05:14.650469
...
```

## Results

I have been testing the `credleaks` script with different models and I have found that the `qwen3:8b` model is the most accurate, at the cost of being slower than other models.

| Test | Model | Time | Result |
|------|-------|------|--------|
| `unbound.conf` | `qwen3:8b`           | 41s | OK |
| `unbound.conf` | `deepseek-r1:7b`     | 29s | OK |
| `unbound.conf` | `qwen2.5-coder:7b`   | 26s | False positive on files |
| `unbound.conf` | `qwen2.5-coder:1.5b` |  8s | False positive on files |
| `unbound.conf` | `llama3.2:latest`    | 11s | False positive on files |

| Test | Model | Time | Result |
|------|-------|------|--------|
| `monit.conf.erb` | `qwen3:8b`           | 35s | OK |
| `monit.conf.erb` | `deepseek-r1:7b`     | 22s | OK |
| `monit.conf.erb` | `qwen2.5-coder:7b`   | 10s | OK |
| `monit.conf.erb` | `qwen2.5-coder:1.5b` |  2s | False negative |
| `monit.conf.erb` | `llama3.2:latest`    |  3s | OK usually, some times false positives on mail or other |
