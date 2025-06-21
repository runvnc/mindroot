import os
import subprocess
from datetime import datetime

async def get_git_version_info(context=None):
    """Get git commit hash and date of last commit.
    
    Returns a dictionary with commit hash and date, or None if not in a git repo.
    
    Example:
    { "get_git_version_info": {} }
    """
    try:
        # Get the current working directory or use a default path
        repo_path = os.getcwd()
        if '/files/mindroot' in repo_path or repo_path.endswith('mindroot'):
            # We're likely in the right place
            pass
        else:
            # Try to find mindroot directory
            if os.path.exists('/files/mindroot'):
                repo_path = '/files/mindroot'
            else:
                return None
        
        # Get commit hash
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return None
            
        commit_hash = result.stdout.strip()
        
        # Get commit date
        result = subprocess.run(
            ['git', 'log', '-1', '--format=%ci'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return None
            
        commit_date = result.stdout.strip()
        
        return {
            'commit_hash': commit_hash,
            'commit_date': commit_date,
            'retrieved_at': datetime.now().isoformat()
        }
        
    except Exception as e:
        return None

