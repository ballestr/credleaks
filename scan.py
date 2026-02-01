#!/usr/bin/env python3
import datetime
import subprocess
import json
import pathlib
import sys
import time

MODEL = "qwen3:8b"
#MODEL = "qwen2.5-coder:1.5b" ## no answers ?
#MODEL = "llama3.2:latest" ## useless, flags too much stuff
MAX_FILE_SIZE = 200_000   # skip huge blobs
RETRIES = 2

PROMPT_TEMPLATE = """You are a static security scanner.

Your task is to identify HARD-CODED SECRETS in the provided file.

A finding MUST meet ALL of the following:
- The value is directly usable as a credential, token, API key, or private key
- The value is present in cleartext in the file
- The value is NOT a placeholder, example, or dummy value
- The value is NOT retrieved from Hiera, Vault, environment variables, or external files

DO NOT flag:
- Variable names or parameter names
- lookup(), hiera(), eyaml, sops, vault references
- Encrypted or hashed values unless clearly marked as a password
- File paths that may contain secrets
- Comments unless they contain an actual usable credential

If there are NO findings, output an empty JSON array: []

Otherwise, output ONLY a JSON array in the following format:

[
  {{
    "file": <filename>,
    "line": <line number>,
    "type": "password|api_key|token|private_key|other",
    "confidence": "high|medium",
    "snippet": "<exact line or minimal snippet>",
    "reason": "<why this is a real secret>"
  }}
]

Do not include any text outside the JSON array.

File path: {path}

File contents:
{content}
"""

def run_ollama(prompt: str) -> str:
    proc = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt,
        text=True,
        capture_output=True,
        timeout=240,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr)
    return proc.stdout.strip()

def extract_json_array(text: str):
    """
    Extract the first top-level JSON array from text.
    Returns a Python list or raises ValueError.
    """
    start = text.rfind("[")
    end = text.rfind("]")

    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON array found")

    snippet = text[start:end + 1]
    return json.loads(snippet)

def scan_file(path: pathlib.Path):
    try:
        content = path.read_text(errors="ignore")
    except Exception:
        return []

    if len(content) > MAX_FILE_SIZE:
        return []

    prompt = PROMPT_TEMPLATE.format(
        path=str(path),
        content=content
    )

    t0 = datetime.datetime.now()
    print(f"## scan {path}",flush=True)
    #return [] ## for testing

    for attempt in range(RETRIES + 1):
        print(f"#### scan {path} attempt {attempt}",flush=True)
        output = None
        findings = []
        try:
            output = run_ollama(prompt)
            findings = extract_json_array(output)
            if isinstance(findings, list):
                print(output)
                break
                #return findings
        except Exception as e:
            if attempt == RETRIES:
                findings = [{
                    "line": None,
                    "type": "error",
                    "confidence": "medium",
                    "snippet": "",
                    "reason": f"LLM failure: {e}"
                }]
                break
            print(f"## Exception: {e}")
            print(output)
            #raise
            time.sleep(1)

    t1 = datetime.datetime.now()
    dt = t1 - t0
    print(f"## done in {dt.total_seconds()} seconds")
    return findings

def scan_dir(results,basepath):
    for path in pathlib.Path(basepath).rglob("*"):
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue

        findings = scan_file(path)
        for f in findings:
            f["file"] = str(path)
            print(f)
            results.append(f)
    return results;

def main(root):
    results = []
    results = scan_dir(results,root)

    json.dump(results, sys.stdout, indent=2)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: scan.py <repo_root>")
        sys.exit(1)
    main(sys.argv[1])
