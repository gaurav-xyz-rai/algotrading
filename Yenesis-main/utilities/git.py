import subprocess

def git_commit(file):
    try:
        # Set Git identity (needed for CI environments)
        subprocess.run(['git', 'config', '--global', 'user.email', 'sindabad764@gmail.com'], check=True)
        subprocess.run(['git', 'config', '--global', 'user.name', 'sindabad764'], check=True)

        # Stage the file
        subprocess.run(['git', 'add', file], check=True)

        # Check if there are any staged changes
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'])
        if result.returncode != 0:
            # Commit only if there are changes
            subprocess.run(['git', 'commit', '-m', f'adding {file}'], check=True)
            print("✅ buy_signal.txt committed successfully.")
            # Push the changes to remote
            subprocess.run(['git', 'push'], check=True)
            print("🚀 Changes pushed to remote repository.")
        else:
            print("ℹ️ No changes to commit in buy_signal.txt.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
