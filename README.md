# AILeek - Local AI Security Scanner

AILeek (`scan.py`) is a static automated security scanner that leverages local Large Language Models (LLMs) via **Ollama** to identify hard-coded secrets in source code and configuration files.

Unlike traditional regex-based scanners, AILeek uses semantic understanding to distinguish between real credentials and false positives like placeholders, variables, or test data.

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
./scan.py .
```

Scan specific files or directories:

```bash
./scan.py src/config.py /etc/myapp/
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `targets` | List of files or directories to scan. | (Required) |
| `--model <name>` | Specify the Ollama model to use. | `qwen2.5-coder:7b` |
| `--max-size <bytes>` | Skip files larger than this size. | `200000` |
| `--show-thinking` | Show the model's reasoning/chain-of-thought (useful for debugging, may break json output). | `False` (hidden) |
| `-h`, `--help` | Show help message. | |

### Examples

Use a specific model (e.g., a smaller coding model):
```bash
./scan.py . --model qwen2.5-coder:1.5b
```

Debug why a model is flagging false positives by seeing its "thinking":
```bash
./scan.py secretive.py --show-thinking
```

## Model Performance

*Values below are experimental observations.*

### qwen2.5-coder:7b
- **Speed**: Moderate.
- **Accuracy**: Good balance. Follows instructions well to output strict JSON.

### qwen2.5-coder:1.5b
- **Speed**: Fast.
- **Accuracy**: Lower. May struggle with complex edge cases or produce malformed JSON.

### llama3.2
- **Speed**: Good.
- **Accuracy**: Tends to be overly cautious, flagging more false positives (variables, placeholders).
