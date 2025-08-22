#!/usr/bin/env python3

import sys
import subprocess
import shutil
from pathlib import Path
import yaml
import tempfile

from rich.console import Console

console = Console()


def check_workflow_file():
    """Check if workflow file exists and is valid YAML"""
    console.print("1. Checking workflow file...")
    
    workflow_file = Path(".github/workflows/firmware-dump.yml")
    if not workflow_file.exists():
        console.print("❌ Workflow file not found", style="red")
        return False
    
    console.print("✅ Workflow file exists")
    
    try:
        with open(workflow_file) as f:
            yaml.safe_load(f)
        console.print("✅ Workflow YAML syntax is valid")
        return True
    except yaml.YAMLError as e:
        console.print(f"❌ Workflow YAML syntax is invalid: {e}", style="red")
        return False


def check_setup_script():
    """Check setup script"""
    console.print("2. Checking setup script...")
    
    setup_script = Path("setup_dumprx.py")
    if setup_script.exists() and setup_script.stat().st_mode & 0o111:
        console.print("✅ Setup script exists and is executable")
        return True
    elif setup_script.exists():
        console.print("✅ Setup script exists")
        return True
    else:
        console.print("❌ Setup script not found", style="red")
        return False


def check_dumprx_package():
    """Check DumprX package"""
    console.print("3. Checking DumprX package...")
    
    if Path("dumprx").exists() and Path("dumprx/__init__.py").exists():
        console.print("✅ DumprX package exists")
        return True
    else:
        console.print("❌ DumprX package not found", style="red")
        return False


def check_git_lfs():
    """Check Git LFS availability"""
    console.print("4. Checking Git LFS...")
    
    if shutil.which("git-lfs"):
        console.print("✅ Git LFS is available")
        return True
    else:
        console.print("❌ Git LFS not found", style="red")
        return False


def test_token_file_logic():
    """Test token file logic"""
    console.print("5. Testing token file logic...")
    
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.test_token') as f:
            f.write("test_token")
            test_file = Path(f.name)
        
        if test_file.exists() and test_file.read_text().strip() == "test_token":
            console.print("✅ Token file creation and reading works")
            test_file.unlink()
            return True
        else:
            console.print("❌ Token file logic failed", style="red")
            return False
            
    except Exception as e:
        console.print(f"❌ Token file logic failed: {e}", style="red")
        return False


def check_gitignore():
    """Check .gitignore"""
    console.print("6. Checking .gitignore...")
    
    gitignore = Path(".gitignore")
    if not gitignore.exists():
        console.print("❌ .gitignore not found", style="red")
        return False
    
    content = gitignore.read_text()
    if "github_token" in content or "gitlab_token" in content:
        console.print("✅ Sensitive files are in .gitignore")
        return True
    else:
        console.print("❌ Token files not properly ignored", style="red")
        return False


def check_documentation():
    """Check documentation"""
    console.print("7. Checking documentation...")
    
    readme = Path("README.md")
    if not readme.exists():
        console.print("❌ README.md not found", style="red")
        return False
    
    readme_content = readme.read_text()
    if "GitHub Actions Workflow Usage" in readme_content:
        console.print("✅ Workflow documentation exists in README")
    else:
        console.print("❌ Workflow documentation missing", style="red")
        return False
    
    workflow_examples = Path("WORKFLOW_EXAMPLES.md")
    if workflow_examples.exists():
        console.print("✅ Workflow examples file exists")
        return True
    else:
        console.print("❌ Workflow examples file missing", style="red")
        return False


def main():
    """Main validation function"""
    console.print("🔍 Validating DumprX Workflow Components...", style="bold blue")
    console.print("=" * 44)
    
    checks = [
        check_workflow_file,
        check_setup_script,
        check_dumprx_package,
        check_git_lfs,
        test_token_file_logic,
        check_gitignore,
        check_documentation
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    console.print("=" * 44)
    
    if all_passed:
        console.print("🎉 All validation checks passed!", style="bold green")
        console.print()
        console.print("Your DumprX repository is ready for the GitHub Actions workflow!", style="green")
        console.print()
        console.print("To use the workflow:", style="cyan")
        console.print("1. Go to the Actions tab in your GitHub repository", style="cyan")
        console.print("2. Select 'Firmware Dump Workflow'", style="cyan")
        console.print("3. Click 'Run workflow'", style="cyan")
        console.print("4. Fill in the required parameters", style="cyan")
        console.print("5. Click 'Run workflow' to start the process", style="cyan")
        sys.exit(0)
    else:
        console.print("❌ Some validation checks failed!", style="bold red")
        sys.exit(1)


if __name__ == "__main__":
    main()