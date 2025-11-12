import os
import re
from typing import List, Dict

# Add any binary extensions you want to skip
BINARY_EXTENSIONS = [
    ".exe", ".dll", ".so", ".bin", ".class", ".jar", ".pyc", ".pyo", ".zip", ".tar", ".gz", ".png", ".jpg", ".jpeg", ".gif"
]

def is_text_file(filename: str) -> bool:
    return not any(filename.endswith(ext) for ext in BINARY_EXTENSIONS)


def extract_code_files(repo_path: str, max_file_size_mb: int = 5) -> List[Dict]:
    """
    Extract all code/text files in the repo with path and content.
    Skips binary files and files exceeding max_file_size_mb.
    """
    code_files = []

    if not os.path.exists(repo_path):
        print(f"❌ Repo path does not exist: {repo_path}")
        return code_files

    for root, _, files in os.walk(repo_path):
        for f in files:
            file_path = os.path.join(root, f)
            if not is_text_file(f):
                continue
            try:
                size_mb = os.path.getsize(file_path) / (1024*1024)
                if size_mb > max_file_size_mb:
                    print(f"⚠️ Skipping large file: {file_path} ({size_mb:.2f} MB)")
                    continue

                with open(file_path, "r", encoding="utf-8", errors="ignore") as file:
                    content = file.read().strip()
                    if content:
                        code_files.append({"path": file_path, "content": content})
            except Exception as e:
                print(f"❌ Failed to read {file_path}: {e}")
                continue

    print(f"🔍 Total code/text files found: {len(code_files)}")
    return code_files


def extract_endpoints_from_code(code_texts: List[str]) -> List[str]:
    """
    Detects API endpoints across multiple languages and frameworks:
      ✅ Python (FastAPI, Flask, Django REST)
      ✅ JavaScript/TypeScript (Express, Axios, Fetch)
      ✅ Java/Kotlin (Spring Boot)
      ✅ Go (Gin, Fiber)
      ✅ Ruby (Rails)
      ✅ PHP (Laravel)
    Returns a list of "METHOD /path".
    """
    endpoints = []

    # Python FastAPI / Flask / Django REST
    py_pattern = r'@[\w_]+\.(get|post|put|delete|patch)\(["\'`]([^"\'`]+)["\'`]\)'

    # Express.js (variable-agnostic)
    js_backend_pattern = r'\b\w+\.(get|post|put|delete|patch)\(\s*[\'"`]([^\'"`]+)[\'"`]'

    # Axios calls
    axios_pattern = r'axios\.(get|post|put|delete|patch)\(\s*[\'"`]([^\'"`]+)[\'"`]'

    # Fetch API
    fetch_pattern = r'fetch\(\s*[\'"`]([^\'"`]+)[\'"`]'

    # Java Spring Boot
    java_pattern = r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\(["\'`]([^"\'`]+)["\'`]\)'

    # Go (Gin, Fiber)
    go_pattern = r'\b(router|r|app|api)\.(GET|POST|PUT|DELETE|PATCH)\(["\'`]([^"\'`]+)["\'`]\)'

    # Ruby on Rails (routes.rb)
    ruby_pattern = r'(get|post|put|delete|patch)\s+[\'"`]([^\'"`]+)[\'"`]'

    # PHP Laravel routes
    php_pattern = r'Route::(get|post|put|delete|patch)\(\s*[\'"`]([^\'"`]+)[\'"`]'

    for code in code_texts:
        for pattern, transform in [
            (py_pattern, lambda m: f"{m[0].upper()} {m[1]}"),
            (js_backend_pattern, lambda m: f"{m[0].upper()} {m[1]}"),
            (axios_pattern, lambda m: f"{m[0].upper()} {m[1]}"),
            (fetch_pattern, lambda m: f"GET {m[0]}"),
            (java_pattern, lambda m: f"{m[0].replace('Mapping','').upper()} {m[1]}"),
            (go_pattern, lambda m: f"{m[1].upper()} {m[2]}"),
            (ruby_pattern, lambda m: f"{m[0].upper()} {m[1]}"),
            (php_pattern, lambda m: f"{m[0].upper()} {m[1]}")
        ]:
            matches = re.findall(pattern, code)
            endpoints.extend([transform(m) for m in matches])

    # Remove duplicates and normalize paths
    endpoints = list(set(endpoints))
    return sorted(endpoints)
