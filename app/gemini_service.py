import asyncio
import os
from google import genai
from dotenv import load_dotenv
from app.rag_utils import retrieve_rag_context

load_dotenv()

# ------------------------------
# Gemini API Client
# ------------------------------
def get_gemini_client():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("🚨 GOOGLE_API_KEY not set in environment!")
    return genai.Client(api_key=api_key)


# ------------------------------
# Analyze single file with RAG context
# ------------------------------
async def analyze_file_with_context(client, file, context):
    """Analyze a single file using AI and RAG context."""
    file_name = file["path"].split("/")[-1]
    code_content = file["content"]

    prompt = f"""
You are a senior software security and code quality auditor.
Analyze this file with context and provide concise, actionable suggestions:
- Detect possible security issues
- Suggest performance or readability improvements
- Mention framework-specific best practices

RAG Context:
{context}

File Name: {file_name}
Code:
{code_content[:3000]}
"""

    try:
        response = await asyncio.to_thread(
            client.models.generate_content,
            model="gemini-2.0-flash",
            contents=prompt
        )

        candidate = response.candidates[0]
        suggestion = ""
        if hasattr(candidate.content, "parts") and len(candidate.content.parts) > 0:
            suggestion = candidate.content.parts[0].text.strip()
        elif isinstance(candidate.content, str):
            suggestion = candidate.content.strip()
        else:
            suggestion = "⚠️ No suggestion returned."

    except Exception as e:
        # Return warning internally but it will be filtered out later
        suggestion = f"⚠️ Failed to analyze file {file_name}: {str(e)}"

    return {"file_name": file_name, "file_path": file["path"], "suggestion": suggestion}


# ------------------------------
# Generate AI suggestions for multiple files
# ------------------------------
# async def generate_ai_suggestions_async(files, vectordb):
#     """
#     Analyze code files with AI, including RAG context.
#     Only returns successful suggestions (filters out failures).
#     """
#     client = get_gemini_client()
#     results = []

#     # Allowed code extensions
#     allowed_extensions = (".py", ".js", ".ts", ".java", ".jsx", ".tsx", ".go", ".php", ".rb", ".cs")

#     # Filter code files
#     filtered_files = [f for f in files if f["path"].lower().endswith(allowed_extensions)]

#     if not filtered_files:
#         return [{"note": "⚠️ No code files found for analysis."}]

#     # Limit to first 2 files to avoid quota/resource issues
#     limited_files = filtered_files[:2]

#     # Run analysis concurrently with RAG context
#     tasks = []
#     for f in limited_files:
#         try:
#             query = f["content"][:500]
#             context = retrieve_rag_context(vectordb, query=query, k=5)
#             tasks.append(analyze_file_with_context(client, f, context))
#         except Exception as e:
#             # Skip files with issues silently
#             print(f"Skipping file {f['name']} due to error preparing context: {e}")

#     # Gather results
#     raw_results = await asyncio.gather(*tasks)

#     # Only keep successful suggestions (filter out failures)
#     for r in raw_results:
#         if r["suggestion"] and not r["suggestion"].startswith("⚠️"):
#             results.append(r)

#     return results


# ------------------------------
# Generate AI project summary
# ------------------------------
def generate_ai_project_summary(endpoints, vectordb):
    """Generate a concise project summary using RAG context."""
    try:
        client = get_gemini_client()

        endpoint_text = "\n".join(endpoints[:10])
        rag_context = retrieve_rag_context(vectordb, query="Project overview", k=5)

        prompt = f"""
You are a software architect assistant.
Based on these API endpoints and RAG context, summarize in 3 sentences:
1. What this project does
2. Who might use it
3. Any potential improvements

RAG Context:
{rag_context}

Endpoints:
{endpoint_text}
"""
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        candidate = response.candidates[0]
        content = ""
        if hasattr(candidate.content, "parts") and len(candidate.content.parts) > 0:
            content = candidate.content.parts[0].text
        elif isinstance(candidate.content, str):
            content = candidate.content
        elif isinstance(candidate, dict):
            content = candidate.get("content", "")
        return content.strip() if content else "⚠️ Summary generation returned empty content."

    except Exception as e:
        return f"⚠️ Summary generation failed: {e}"



# ------------------------------
# Generate AI Endpoint Explanations
# ------------------------------
# def generate_ai_endpoint_explanations(endpoints, vectordb):
#     """Explain each API endpoint in human-readable form using RAG context."""
#     if not endpoints:
#         return [{"note": "⚠️ No endpoints found in the project."}]

#     try:
#         client = get_gemini_client()
#         rag_context = retrieve_rag_context(vectordb, query="API routes and controllers", k=5)
#         endpoint_text = "\n".join(endpoints[:50])  # limit for efficiency

#         # --- FIXED PROMPT ---
#         prompt = (
#             "You are a senior backend engineer.\n"
#             "Given these API endpoints and project context, explain what each endpoint likely does.\n"
#             "Provide your answer in JSON array format.\n\n"
#             "RAG Context:\n"
#             f"{rag_context}\n\n"
#             "Endpoints:\n"
#             f"{endpoint_text}\n\n"
#             "Expected JSON output format:\n"
#             "[\n"
#             "  {{\"endpoint\": \"GET /users\", \"description\": \"Fetches all users from database.\"}},\n"
#             "  {{\"endpoint\": \"POST /login\", \"description\": \"Authenticates user and returns JWT token.\"}}\n"
#             "]\n"
#         )

#         response = client.models.generate_content(
#             model="gemini-2.0-flash",
#             contents=prompt
#         )

#         candidate = response.candidates[0]
#         text = ""
#         if hasattr(candidate.content, "parts") and len(candidate.content.parts) > 0:
#             text = candidate.content.parts[0].text.strip()
#         elif isinstance(candidate.content, str):
#             text = candidate.content.strip()

#         # Try to parse valid JSON
#         import json
#         try:
#             return json.loads(text)
#         except Exception:
#             # If not valid JSON, return raw text
#             return [{"endpoint_explanation_text": text}]

#     except Exception as e:
#         return [{"error": f"⚠️ Endpoint explanation failed: {e}"}]



def generate_ai_endpoint_explanations(endpoints, vectordb):
    """Explain each API endpoint in human-readable form using RAG context."""
    if not endpoints:
        return [{"note": "⚠️ No endpoints found in the project."}]

    try:
        client = get_gemini_client()
        rag_context = retrieve_rag_context(vectordb, query="API routes and controllers", k=5)
        endpoint_text = "\n".join(endpoints[:50])  # limit for efficiency

        # Prompt for JSON output with explanation per endpoint
        prompt = (
            "You are a senior backend engineer.\n"
            "Given these API endpoints and project context, explain what each endpoint does.\n"
            "Provide your answer in JSON array format, with each element containing both the endpoint and its explanation.\n\n"
            "RAG Context:\n"
            f"{rag_context}\n\n"
            "Endpoints:\n"
            f"{endpoint_text}\n\n"
            "Expected JSON output format:\n"
            "[\n"
            "  {\"endpoint\": \"GET /users\", \"endpoint_explanation_text\": \"Fetches all users from database.\"},\n"
            "  {\"endpoint\": \"POST /login\", \"endpoint_explanation_text\": \"Authenticates user and returns JWT token.\"}\n"
            "]\n"
        )

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        candidate = response.candidates[0]
        text = ""
        if hasattr(candidate.content, "parts") and len(candidate.content.parts) > 0:
            text = candidate.content.parts[0].text.strip()
        elif isinstance(candidate.content, str):
            text = candidate.content.strip()

        import json
        try:
            # Parse JSON to return structured endpoint + explanation
            return json.loads(text)
        except Exception:
            # If parsing fails, wrap the raw text
            return [{"endpoint": ep, "endpoint_explanation_text": text} for ep in endpoints]

    except Exception as e:
        return [{"endpoint": ep, "endpoint_explanation_text": f"⚠️ Endpoint explanation failed: {e}"} for ep in endpoints]



# ------------------------------
# Generate AI Language Summary (Frontend / Backend / Fullstack)
# ------------------------------
def generate_ai_language_summary(languages, framework, code_texts, vectordb):
    """Use AI to classify project type (frontend, backend, full stack) and explain it."""
    try:
        client = get_gemini_client()
        rag_context = retrieve_rag_context(vectordb, query="project architecture", k=5)
        sample_code = "\n".join(code_texts[:3])[:2000]

        prompt = f"""
You are a software architect.
Given the following details, determine if this project is a frontend, backend, or full-stack app.

Languages: {languages}
Framework: {framework}

Sample Code:
{sample_code}

RAG Context:
{rag_context}

Explain briefly what kind of project this is, what its layers do, and which technologies are responsible for each part.
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        candidate = response.candidates[0]
        text = candidate.content.parts[0].text if hasattr(candidate.content, "parts") else candidate.content
        return text.strip()

    except Exception as e:
        return f"⚠️ Language summary generation failed: {e}"


# ------------------------------
# Generate AI pom.xml Explanation
# ------------------------------
def generate_ai_pom_explanation(pom_content, vectordb):
    """Explain Maven pom.xml file, dependencies, and version info."""
    try:
        client = get_gemini_client()
        rag_context = retrieve_rag_context(vectordb, query="pom.xml dependencies", k=5)

        prompt = f"""
You are a Java build expert.
Analyze this pom.xml and provide a clear explanation:
- Describe the project version (and if it uses mod/scm versions)
- List major dependencies with purpose
- Mention plugin configurations and what they do
- Point out any outdated or risky versions

RAG Context:
{rag_context}

pom.xml:
{pom_content[:6000]}
"""

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        candidate = response.candidates[0]
        text = candidate.content.parts[0].text if hasattr(candidate.content, "parts") else candidate.content
        return text.strip()

    except Exception as e:
        return f"⚠️ pom.xml explanation failed: {e}"

