#!/usr/bin/env python3
"""
git_commit_push.py – Auto-commit and push changes to GitHub.
"""

import subprocess
import sys
from datetime import datetime

def git_commit_push():
    """Commit and push all changes."""
    def git_command(args):
        try:
            result = subprocess.run(
                ['git'] + args,
                capture_output=True,
                text=True,
                check=False
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, '', str(e)
    
    # Check if there are changes
    success, stdout, stderr = git_command(['status', '--porcelain'])
    if not success:
        print(f"⚠️ Git status failed: {stderr}")
        return
    
    if not stdout.strip():
        print("✅ No changes to commit")
        return
    
    # Add all changes
    success, _, stderr = git_command(['add', '.'])
    if not success:
        print(f"⚠️ Git add failed: {stderr}")
        return
    
    # Commit
    message = f"Automated cathedral system update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    success, _, stderr = git_command(['commit', '-m', message])
    if not success:
        print(f"⚠️ Git commit failed: {stderr}")
        return
    
    # Push
    success, _, stderr = git_command(['push', 'origin', 'main'])
    if not success:
        print(f"⚠️ Git push failed: {stderr}")
        return
    
    print("✅ Changes committed and pushed")

if __name__ == "__main__":
    git_commit_push()
