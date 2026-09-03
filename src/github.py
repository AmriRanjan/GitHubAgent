# src/github.py

import base64

import os
import requests
from dotenv import load_dotenv
from langchain_core.documents import Document

load_dotenv()

github_token = os.getenv("GITHUB_TOKEN")

def fetch_github(owner, repo, endpoint):
    url = f"https://api.github.com/repos/{owner}/{repo}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {github_token}"
    }
    response = requests.get(url, headers = headers)

    if response.status_code == 200:
        data = response.json()
        return data
    
    print("Failed with status code:", response.status_code)
    return None

def fetch_github_issues(owner, repo):
    data = fetch_github(owner, repo, "issues")
    if data is None:
        return None
    return load_issues(data)

def load_issues(issues):
    docs = []
    for entry in issues:
        metadata = {
            "author": entry["user"]["login"],
            "comments": entry["comments"],
            "body": entry["body"],
            "labels": entry["labels"],
            "created_at": entry["created_at"],
        }
        new_file = entry["title"]
        if entry["body"]:
            new_file += entry["body"]
        doc = Document(page_content = new_file, metadata = metadata)
        docs.append(doc)
        
    return docs

def fetch_default_branch(owner, repo):
    url = f"https://api.github.com/repos/{owner}/{repo}"

    headers = {
        "Authorization": f"Bearer {github_token}"
    }

    response = requests.get(url, headers = headers)

    if response.status_code == 200:
        data = response.json()
        return data["default_branch"]

    print("Failed with status code:", response.status_code)
    return None

def fetch_repo_tree(owner, repo, branch):
    data = fetch_github(owner, repo, f"git/trees/{branch}?recursive=true")

    if data is None:
        return None

    return data["tree"]

def filter_code_files(tree):
    allowed_extensions = (
        ".py",
        ".js",
        ".ts",
        ".java",
        ".cpp",
        ".c",
        ".h",
        ".cs",
        ".go",
        ".rs",
        ".php",
        ".rb",
        ".swift",
        ".kt",
        ".html",
        ".css",
        ".md",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
    )

    ignored_directories = (
        ".git/",
        "venv/",
        ".venv/",
        "node_modules/",
        "__pycache__/",
    )

    files = []

    for item in tree:
        if item["type"] != "blob":
            continue

        path = item["path"]

        if path.startswith(ignored_directories):
            continue

        if path.endswith(allowed_extensions):
            files.append(path)

    return files

def fetch_file(owner, repo, path, branch):
    data = fetch_github(owner, repo, f"contents/{path}?ref={branch}")

    if data is None:
        return None

    content = data["content"]

    decoded_content = base64.b64decode(content).decode("utf-8")

    return decoded_content

def load_code(owner, repo, branch, files):
    docs = []

    for path in files:
        content = fetch_file(owner, repo, path, branch)

        metadata = {
            "path": path,
            "branch": branch
        }

        doc = Document(
            page_content = content,
            metadata = metadata
        )

        docs.append(doc)

    return docs