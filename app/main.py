# import os
# import shutil
# from fastapi import FastAPI, Form
# from fastapi.middleware.cors import CORSMiddleware
# from app.github_utils import clone_github_repo
# from app.code_parser import extract_code_files, extract_endpoints_from_code
# from app.rag_utils import create_rag_vectorstore
# from app.gemini_service import (
#     generate_ai_suggestions_async,
#     generate_ai_project_summary,
#     generate_ai_endpoint_explanations,
#     generate_ai_language_summary,
#     generate_ai_pom_explanation
# )

# app = FastAPI(title="Smart API DocGen (Full RAG)", version="3.0")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --- Helper Functions ---
# def classify_project_from_files(code_files):
#     combined_paths = " ".join([f["path"].lower() for f in code_files])
#     combined_code = " ".join([f["content"].lower()[:1000] for f in code_files])
#     languages, framework = [], "Unknown"

#     if ".py" in combined_paths:
#         languages.append("Python")
#     if ".ts" in combined_paths or ".js" in combined_paths:
#         languages.append("TypeScript/JavaScript")
#     if ".java" in combined_paths:
#         languages.append("Java")
#     if ".php" in combined_paths:
#         languages.append("PHP")
#     if ".cs" in combined_paths:
#         languages.append("C#")

#     if "angular" in combined_paths or "component" in combined_paths:
#         framework = "Angular"
#     elif "react" in combined_paths:
#         framework = "React"
#     elif "flask" in combined_code:
#         framework = "Flask"
#     elif "springboot" in combined_code or "@restcontroller" in combined_code:
#         framework = "Spring Boot"
#     elif "express" in combined_code:
#         framework = "Express.js"

#     return {"languages": languages or ["Unknown"], "framework": framework}

# def get_relative_path(file_path, repo_name):
#     if repo_name in file_path:
#         return file_path.split(repo_name, 1)[-1].lstrip("/")
#     return os.path.basename(file_path)

# # --- Main Endpoint ---
# @app.post("/generate-docs")
# async def generate_docs(git_url: str = Form(...)):
#     repo_path = clone_github_repo(git_url)
#     repo_name = git_url.split("/")[-1].replace(".git", "")

#     code_files = extract_code_files(repo_path)
#     if not code_files:
#         shutil.rmtree(repo_path)
#         return {"status": "error", "message": "No code files found in repo."}

#     allowed_exts = (".py", ".js", ".ts", ".jsx", ".java", ".kt", ".c", ".cpp")
#     filtered_files = [f for f in code_files if f["path"].endswith(allowed_exts)]
#     if not filtered_files:
#         shutil.rmtree(repo_path)
#         return {"status": "error", "message": "No source code files found for analysis."}

#     # --- RAG Vectorstore ---
#     vectordb = create_rag_vectorstore([f["content"] for f in filtered_files])

#     # --- Extract endpoints ---
#     endpoints = extract_endpoints_from_code([f["content"] for f in filtered_files])

#     # --- Generate AI suggestions with RAG context ---
#     suggestions = await generate_ai_suggestions_async(filtered_files, vectordb)
#     for s in suggestions:
#         s["file_path"] = get_relative_path(s["file_path"], repo_name)
#         s["file_name"] = os.path.basename(s["file_path"])

#     # --- Classify project + AI summary ---
#     project_info = classify_project_from_files(filtered_files)
#     ai_summary = generate_ai_project_summary(endpoints, vectordb)

#     # --- Cleanup ---
#     shutil.rmtree(repo_path)

#     return {
#         "status": "success",
#         "project_info": {
#             "name": repo_name,
#             "languages": project_info["languages"],
#             "framework": project_info["framework"]
#         },
#         "endpoints": endpoints,
#         "ai_project_summary": ai_summary,
#         "suggestions": suggestions,
#         "note": "⚡ All code files analyzed using RAG context."
#     }



import os

# ✅ Prevent Hugging Face tokenizers warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import shutil
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware

from app.github_utils import clone_github_repo
from app.code_parser import extract_code_files, extract_endpoints_from_code
from app.rag_utils import create_rag_vectorstore
from app.gemini_service import (
    # generate_ai_suggestions_async,
    generate_ai_project_summary,
    generate_ai_endpoint_explanations,
    generate_ai_language_summary,
    generate_ai_pom_explanation
)

# ------------------------------------------------------------------
# FastAPI Initialization
# ------------------------------------------------------------------
app = FastAPI(title="Smart API DocGen (Full RAG)", version="3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------
def classify_project_from_files(code_files):
    """Detects primary languages and framework from file structure and content."""
    combined_paths = " ".join([f["path"].lower() for f in code_files])
    combined_code = " ".join([f["content"].lower()[:1000] for f in code_files])
    languages, framework = [], "Unknown"

    # Detect languages
    if ".py" in combined_paths:
        languages.append("Python")
    if ".ts" in combined_paths or ".js" in combined_paths:
        languages.append("TypeScript/JavaScript")
    if ".java" in combined_paths:
        languages.append("Java")
    if ".php" in combined_paths:
        languages.append("PHP")
    if ".cs" in combined_paths:
        languages.append("C#")

    # Detect frameworks
    if "angular" in combined_paths or "component" in combined_paths:
        framework = "Angular"
    elif "react" in combined_paths:
        framework = "React"
    elif "flask" in combined_code:
        framework = "Flask"
    elif "springboot" in combined_code or "@restcontroller" in combined_code:
        framework = "Spring Boot"
    elif "express" in combined_code:
        framework = "Express.js"

    return {"languages": languages or ["Unknown"], "framework": framework}


def get_relative_path(file_path, repo_name):
    """Normalize file paths for readability in response."""
    if repo_name in file_path:
        return file_path.split(repo_name, 1)[-1].lstrip("/")
    return os.path.basename(file_path)


# ------------------------------------------------------------------
# Main Endpoint: /generate-docs
# ------------------------------------------------------------------
@app.post("/generate-docs")
async def generate_docs(git_url: str = Form(...)):
    """
    Clone the given GitHub repo, analyze code using AI (Gemini + RAG),
    and return a detailed documentation report including:
    - Project language & framework
    - API endpoints & explanations
    - pom.xml insights (for Java projects)
    - AI-driven improvement suggestions
    """
    # --- Clone repo ---
    repo_path = clone_github_repo(git_url)
    repo_name = git_url.split("/")[-1].replace(".git", "")

    # --- Extract code/text files ---
    code_files = extract_code_files(repo_path)
    if not code_files:
        shutil.rmtree(repo_path)
        return {"status": "error", "message": "No code files found in repo."}

    # --- Filter source files ---
    allowed_exts = (".py", ".js", ".ts", ".jsx", ".java", ".kt", ".c", ".cpp", ".php", ".rb")
    filtered_files = [f for f in code_files if f["path"].endswith(allowed_exts)]
    if not filtered_files:
        shutil.rmtree(repo_path)
        return {"status": "error", "message": "No source code files found for analysis."}

    # --- Create RAG vectorstore ---
    vectordb = create_rag_vectorstore([f["content"] for f in filtered_files])

    # --- Extract API endpoints ---
    endpoints = extract_endpoints_from_code([f["content"] for f in filtered_files])
    endpoint_explanations = generate_ai_endpoint_explanations(endpoints, vectordb)

    # --- Generate AI suggestions with RAG context ---
    # suggestions = await generate_ai_suggestions_async(filtered_files, vectordb)
    # for s in suggestions:
    #     s["file_path"] = get_relative_path(s["file_path"], repo_name)
    #     s["file_name"] = os.path.basename(s["file_path"])

    # --- Classify project type ---
    project_info = classify_project_from_files(filtered_files)

    # ✅ Add retry logic for rate limits
    import time
    for attempt in range(3):  # Try up to 3 times
        try:
            language_summary = generate_ai_language_summary(
                project_info["languages"],
                project_info["framework"],
                [f["content"] for f in filtered_files],
                vectordb
            )
            break  # success → exit loop
        except Exception as e:
            if "RESOURCE_EXHAUSTED" in str(e):
                print(f"⚠️ Attempt {attempt+1} failed: rate limit hit. Retrying in 30s...")
                time.sleep(30)
            else:
                raise
    else:
        # If all 3 attempts failed
        language_summary = "⚠️ AI summary temporarily unavailable (rate limit). Try again later."


    # --- AI project summary ---
    ai_summary = generate_ai_project_summary(endpoints, vectordb)

    # --- pom.xml analysis ---
    pom_path = next((f["path"] for f in code_files if f["path"].endswith("pom.xml")), None)
    pom_explanation = None
    if pom_path:
        try:
            with open(pom_path, "r", encoding="utf-8", errors="ignore") as pom_file:
                pom_content = pom_file.read()
            pom_explanation = generate_ai_pom_explanation(pom_content, vectordb)
        except Exception as e:
            pom_explanation = f"⚠️ Failed to analyze pom.xml: {e}"

    # --- Cleanup cloned repo ---
    shutil.rmtree(repo_path)

    # --- Final structured response ---
    return {
        "status": "success",
        "project_info": {
            "name": repo_name,
            "languages": project_info["languages"],
            "framework": project_info["framework"],
            "ai_language_summary": language_summary,
        },
        "endpoints": endpoints,
        "endpoint_explanations": endpoint_explanations,
        "ai_project_summary": ai_summary,
        "pom_explanation": pom_explanation,
        # "suggestions": suggestions,
        "note": "⚡ All code files analyzed using RAG context and AI-enhanced insights."
    }
