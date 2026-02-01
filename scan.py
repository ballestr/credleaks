#!/usr/bin/env python3
import datetime
import subprocess
import json
import pathlib
import sys
import time
import argparse

#MODEL = "qwen3:8b" ## works but is slow
#MODEL = "qwen2.5-coder:1.5b" ## no answers ?
MODEL = "qwen2.5-coder:7b" ## 
#MODEL = "llama3.2:latest" ## useless, flags too much stuff
MAX_FILE_SIZE = 200_000   # skip huge blobs
RETRIES = 2
SHOW_THINKING = False

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
    "line": <line number>,
    "type": "password|api_key|token|private_key|other",
    "confidence": "high|medium",
    "snippet": "<exact line or minimal snippet, no newlines>",
    "reason": "<why this is a real secret>"
  }}
]

Do not include any text outside the JSON array.

File path: {path}

File contents:
{content}
"""

class ScannerError(Exception):
    pass

def ts():
    return f"{datetime.datetime.now():%H:%M:%S}"

def run_ollama(prompt: str) -> str:
    if MODEL == "dummy":
        return "[]"
    try:
        cmd = ["ollama", "run"]
        if not SHOW_THINKING:
            cmd.append("--hidethinking")
        cmd.append(MODEL)
        
        proc = subprocess.run(
            cmd,
            input=prompt,
            text=True,
            capture_output=True,
            timeout=240,
        )
        if proc.returncode != 0:
            raise ScannerError(f"Ollama Error: {proc.stderr.strip()}")
        return proc.stdout.strip()
    except subprocess.TimeoutExpired:
        raise ScannerError("Ollama request timed out")
    except FileNotFoundError:
        raise ScannerError("Ollama binary not found in PATH")

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
    print(f"{ts()} ## scan {path}",flush=True)
    #return [] ## for testing

    for attempt in range(RETRIES + 1):
        if attempt > 0 :
            print(f"{ts()} ## scan {path} attempt {attempt}",flush=True)
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
    issues = "OK" if len(findings)==0 else f"issues {len(findings)}"
    print(f"{ts()} ## done {path} in {dt.total_seconds()} seconds {issues}")
    return findings

def scan_targets(results, paths):
    stats = {
        "scanned": 0,
        "files_with_issues": 0,
        "total_issues": 0,
        "errors": 0
    }
    
    def generate_paths(paths):
        for p in paths:
            path = pathlib.Path(p)
            if path.is_file():
                yield path
            elif path.is_dir():
                yield from sorted(path.rglob("*"))

    for path in generate_paths(paths):
        if path.is_symlink():
            continue
        if not path.is_file():
            continue
        if ".git" in path.parts:
            continue

        stats["scanned"] += 1
        findings = scan_file(path)
        
        has_error = any(f.get("type") == "error" for f in findings)
        if has_error:
            stats["errors"] += 1
            
        real_findings = [f for f in findings if f.get("type") != "error"]
        if real_findings:
            stats["files_with_issues"] += 1
            stats["total_issues"] += len(real_findings)

        for f in findings:
            f["file"] = str(path)
            print(f)
            results.append(f)
    return results, stats

def main():
    global MODEL, MAX_FILE_SIZE, SHOW_THINKING
    parser = argparse.ArgumentParser(description="AI Static Security Scanner")
    parser.add_argument("targets", nargs='+', help="File(s) or directories to scan")
    parser.add_argument("--model", default=MODEL, help=f"Ollama model (default: {MODEL})")
    parser.add_argument("--max-size", type=int, default=MAX_FILE_SIZE, dest="max_size", help=f"Max file size (default: {MAX_FILE_SIZE})")
    parser.add_argument("--show-thinking", action="store_true", help="Show model thinking/reasoning process")
    
    args = parser.parse_args()

    # Update globals
    MODEL = args.model
    MAX_FILE_SIZE = args.max_size
    SHOW_THINKING = args.show_thinking
    
    targets = args.targets

    print(f"{ts()} aileeks using ollama model {MODEL}",flush=True)
    results = []
    stats = {}
    t_start = datetime.datetime.now()
    try:
        results, stats = scan_targets(results,targets)
        print(f"{ts()} ## scan completed")
    except (KeyboardInterrupt, BrokenPipeError):
        print(f"{ts()} ## scan interrupted")
    
    t_end = datetime.datetime.now()
    total_time = t_end - t_start

    print(f"{ts()} ## Summary: scanned={stats.get('scanned', 0)} files_with_issues={stats.get('files_with_issues', 0)} total_issues={stats.get('total_issues', 0)} errors={stats.get('errors', 0)} total_time={total_time}")
    #
    print("----"*20)
    json.dump(results, sys.stdout, indent=2)

if __name__ == "__main__":
    main()
