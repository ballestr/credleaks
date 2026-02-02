# CredLeaks - Local AI Security Scanner

CredLeaks (`credleaks`) is a static automated security scanner that leverages local Large Language Models (LLMs) via **Ollama** to identify hard-coded secrets in source code and configuration files.

Unlike traditional regex-based scanners like [gitleaks](https://github.com/gitleaks/gitleaks), CredLeaks uses the semantic understanding of LLMs to distinguish between real credentials and false positives like placeholders, variables, or test data, and to find secrets in less obvious places that do not match simple patterns.

Using local LLMs ensures that no code is sent to the cloud, and that the scanner can be run in air-gapped environments. You can use this to sanitize your code before starting to work on it with a cloud-based AI assistant.

## Features

- **Local Processing**: Runs entirely on your machine using Ollama; no code is sent to the cloud.
- **Context Aware**: Uses LLMs to understand the context of a potential secret.
- **Configurable**: Supports any model available in your Ollama library.
- **JSON Output**: Produces structured JSON output for easy integration with other tools.
- **Summary Statistics**: Provides a quick overview of scan results, errors, and timing.

## Prerequisites

- **Python 3.x**
- **[Ollama](https://ollama.com/)** installed and running (`ollama serve`).
- At least one LLM pulled (e.g., `ollama pull qwen2.5-coder:7b`).

## Usage

Basic usage scanning the current directory:

```bash
./credleaks .
```

Scan specific files or directories:

```bash
./credleaks src/config.py /etc/myapp/
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `targets` | List of files or directories to scan. | (Required) |
| `--model <name>` | Specify the Ollama model to use. | `qwen3:8b` |
| `--max-size <bytes>` | Skip files larger than this size. | `200000` |
| `--show-thinking` | Show the model's reasoning/chain-of-thought (useful for debugging, may break json output). | `False` (hidden) |
| `-h`, `--help` | Show help message. | |

### Examples

Use a specific model (e.g., a smaller coding model):
```bash
./credleaks . --model qwen2.5-coder:1.5b
```

Debug why a model is flagging false positives by seeing its "thinking":
```bash
./credleaks secretive.py --show-thinking
```

## Model Performance

I have managed to get good results with some thinking model that fits on my 16GB RAM Macbook air M2.
The non-thinking models are faster but produce more false positives. See the [README_tests.md](README_tests.md) for more details.

### qwen3:8b
- **Speed**: Slow, around 60 seconds per file on a Macbook Air M2.
- **Accuracy**: Good balance. Follows instructions well to output strict JSON.

### deepseek-r1:7b
- **Speed**: Slow, just slightly faster than qwen3:8b.
- **Accuracy**: Good. Follows instructions well to output strict JSON.

### qwen2.5-coder:1.5b
- **Speed**: Fast.
- **Accuracy**: Lower. May struggle with complex edge cases or produce malformed JSON.

### qwen2.5-coder:7b
- **Speed**: Slower than qwen2.5-coder:1.5b.
- **Accuracy**: Not much better than qwen2.5-coder:1.5b.

### llama3.2
- **Speed**: Good.
- **Accuracy**: Tends to be overly cautious, flagging more false positives (variables, placeholders).

## History

This started with the wish to use AI coding agents on a codebasefor system configuration management that has a very long history. Using gitleaks worked pretty well but failed to find less obvious secrets. Writing more regexes was still not going to work, because of the wide variety of file types and languages.

The initial attempts to prompt `opencode` using local LLMs failed, the agent was soon forgetting which files it had considered and which it had not. So I asked ChatGPT how to get better results and it suggested to use a script to call directly the LLM for each file, and to use a very prescriptive prompt.

The first version, with prompt and python produced entirely by ChatGPT, already produced interesting results. Afterwards I have refined the script with the help of Antigravity, collected some test cases and compared the results of different models.
