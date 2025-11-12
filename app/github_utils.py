# app/github_utils.py
import git
import tempfile
import os

def clone_github_repo(repo_url: str) -> str:
    """
    Clones the given GitHub repository into a temporary directory.
    
    Args:
        repo_url (str): GitHub repository URL.
    
    Returns:
        str: Path to the cloned repository.
    """
    temp_dir = tempfile.mkdtemp()
    git.Repo.clone_from(repo_url, temp_dir)
    return temp_dir
