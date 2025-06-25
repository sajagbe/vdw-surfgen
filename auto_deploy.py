#!/usr/bin/env python3
"""
Automated deployment script for vdw-surfgen package.
Handles version bumping, building, and uploading to GitHub and PyPI.
"""

import os
import sys
import subprocess
import re
from pathlib import Path
from datetime import datetime
import argparse
from colorama import init, Fore, Style, Back
import time

# Initialize colorama
init(autoreset=True)

class AutoDeploy:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.pyproject_file = self.project_root / "pyproject.toml"
        self.setup_file = self.project_root / "setup.py"
        
    def print_header(self, message):
        """Print a colorful header message."""
        print(f"\n{Back.BLUE}{Fore.WHITE} 🚀 {message} 🚀 {Style.RESET_ALL}\n")
        
    def print_success(self, message):
        """Print a success message."""
        print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")
        
    def print_error(self, message):
        """Print an error message."""
        print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")
        
    def print_info(self, message):
        """Print an info message."""
        print(f"{Fore.CYAN}ℹ️  {message}{Style.RESET_ALL}")
        
    def run_command(self, cmd, description=None, capture_output=False):
        """Run a shell command with error handling."""
        if description:
            self.print_info(f"{description}...")
            
        try:
            if capture_output:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=self.project_root)
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(result.returncode, cmd, result.stderr)
                return result.stdout.strip()
            else:
                result = subprocess.run(cmd, shell=True, check=True, cwd=self.project_root)
                return True
        except subprocess.CalledProcessError as e:
            self.print_error(f"Command failed: {cmd}")
            if hasattr(e, 'stderr') and e.stderr:
                self.print_error(f"Error: {e.stderr}")
            return False
    
    def get_current_version(self):
        """Get the current version from pyproject.toml or setup.py."""
        version = None
        
        # Try pyproject.toml first
        if self.pyproject_file.exists():
            with open(self.pyproject_file, 'r') as f:
                content = f.read()
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    version = match.group(1)
        
        # Fallback to setup.py
        if not version and self.setup_file.exists():
            with open(self.setup_file, 'r') as f:
                content = f.read()
                match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
                if match:
                    version = match.group(1)
        
        return version
    
    def bump_version(self, bump_type='patch'):
        """Bump version number (patch, minor, or major)."""
        current_version = self.get_current_version()
        if not current_version:
            self.print_error("Could not find current version")
            return None
            
        self.print_info(f"Current version: {current_version}")
        
        # Parse version
        parts = current_version.split('.')
        if len(parts) != 3:
            self.print_error("Version must be in format X.Y.Z")
            return None
            
        major, minor, patch = map(int, parts)
        
        # Bump version based on type
        if bump_type == 'major':
            major += 1
            minor = 0
            patch = 0
        elif bump_type == 'minor':
            minor += 1
            patch = 0
        else:  # patch
            patch += 1
            
        new_version = f"{major}.{minor}.{patch}"
        
        # Update version in files
        self.update_version_in_files(current_version, new_version)
        
        self.print_success(f"Version bumped: {current_version} → {new_version}")
        return new_version
    
    def update_version_in_files(self, old_version, new_version):
        """Update version in pyproject.toml and setup.py."""
        # Update pyproject.toml
        if self.pyproject_file.exists():
            with open(self.pyproject_file, 'r') as f:
                content = f.read()
            
            content = re.sub(
                rf'version\s*=\s*["\']({re.escape(old_version)})["\']',
                f'version = "{new_version}"',
                content
            )
            
            with open(self.pyproject_file, 'w') as f:
                f.write(content)
                
        # Update setup.py
        if self.setup_file.exists():
            with open(self.setup_file, 'r') as f:
                content = f.read()
            
            content = re.sub(
                rf'version\s*=\s*["\']({re.escape(old_version)})["\']',
                f'version="{new_version}"',
                content
            )
            
            with open(self.setup_file, 'w') as f:
                f.write(content)
    
    def check_git_status(self):
        """Check if there are uncommitted changes."""
        try:
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  capture_output=True, text=True, cwd=self.project_root)
            return result.stdout.strip() != ""
        except:
            return False
    
    def commit_and_push(self, version, commit_message=None):
        """Commit changes and push to GitHub."""
        self.print_header("Committing and Pushing to GitHub")
        
        if not commit_message:
            commit_message = f"🚀 Release v{version}"
        
        # Add all changes
        if not self.run_command("git add .", "Adding all changes"):
            return False
            
        # Commit changes
        if not self.run_command(f'git commit -m "{commit_message}"', "Committing changes"):
            self.print_info("No changes to commit")
            
        # Create and push tag
        tag_name = f"v{version}"
        if not self.run_command(f'git tag {tag_name}', f"Creating tag {tag_name}"):
            self.print_info("Tag might already exist")
            
        # Push to origin
        if not self.run_command("git push origin main", "Pushing to GitHub"):
            return False
            
        # Push tags
        if not self.run_command("git push origin --tags", "Pushing tags"):
            return False
            
        self.print_success("Successfully pushed to GitHub")
        return True
    
    def clean_build(self):
        """Clean previous build artifacts."""
        self.print_info("Cleaning previous build artifacts")
        
        # Remove build directories
        for dir_name in ['build', 'dist', '*.egg-info']:
            self.run_command(f"rm -rf {dir_name}", capture_output=True)
    
    def build_package(self):
        """Build the package."""
        self.print_header("Building Package")
        
        self.clean_build()
        
        # Try using build module first
        if self.run_command("python -m build", "Building with python -m build"):
            self.print_success("Package built successfully with build module")
            return True
            
        # Fallback to setup.py
        if self.run_command("python setup.py sdist bdist_wheel", "Building with setup.py"):
            self.print_success("Package built successfully with setup.py")
            return True
            
        self.print_error("Failed to build package")
        return False
    
    def upload_to_pypi(self, test_pypi=False):
        """Upload package to PyPI or TestPyPI."""
        repo_name = "TestPyPI" if test_pypi else "PyPI"
        self.print_header(f"Uploading to {repo_name}")
        
        # Check package first
        if not self.run_command("python -m twine check dist/*", "Checking package"):
            return False
            
        # Upload command
        if test_pypi:
            upload_cmd = "python -m twine upload --repository testpypi dist/*"
        else:
            upload_cmd = "python -m twine upload dist/*"
            
        if self.run_command(upload_cmd, f"Uploading to {repo_name}"):
            self.print_success(f"Successfully uploaded to {repo_name}")
            return True
        else:
            self.print_error(f"Failed to upload to {repo_name}")
            return False
    
    def install_dependencies(self):
        """Install required build dependencies."""
        self.print_info("Installing build dependencies...")
        
        dependencies = ['build', 'twine', 'wheel']
        for dep in dependencies:
            self.run_command(f"pip install {dep}", f"Installing {dep}", capture_output=True)
    
    def run_tests(self):
        """Run tests if they exist."""
        test_files = list(self.project_root.glob("test*.py")) + list(self.project_root.glob("*test*.py"))
        if test_files:
            self.print_header("Running Tests")
            for test_file in test_files:
                if not self.run_command(f"python {test_file}", f"Running {test_file.name}"):
                    return False
            self.print_success("All tests passed")
        return True
    
    def full_deploy(self, bump_type='patch', test_pypi=False, skip_tests=False, commit_message=None):
        """Run the full deployment pipeline."""
        self.print_header("Starting Automated Deployment")
        
        # Install dependencies
        self.install_dependencies()
        
        # Run tests
        if not skip_tests and not self.run_tests():
            self.print_error("Tests failed, aborting deployment")
            return False
        
        # Check for uncommitted changes
        if self.check_git_status():
            self.print_info("Found uncommitted changes, will include in deployment")
        
        # Bump version
        new_version = self.bump_version(bump_type)
        if not new_version:
            return False
        
        # Build package
        if not self.build_package():
            return False
        
        # Commit and push to GitHub
        if not self.commit_and_push(new_version, commit_message):
            self.print_error("Failed to push to GitHub, but continuing...")
        
        # Upload to PyPI
        if not self.upload_to_pypi(test_pypi):
            return False
        
        self.print_header("🎉 Deployment Completed Successfully! 🎉")
        self.print_success(f"Version {new_version} deployed to {'TestPyPI' if test_pypi else 'PyPI'}")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Automated deployment script for vdw-surfgen",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python auto_deploy.py                    # Patch version bump and deploy
  python auto_deploy.py --minor            # Minor version bump
  python auto_deploy.py --major            # Major version bump
  python auto_deploy.py --test-pypi        # Deploy to TestPyPI first
  python auto_deploy.py --skip-tests       # Skip running tests
  python auto_deploy.py -m "Custom commit message"
        """
    )
    
    parser.add_argument('--patch', action='store_true', default=True,
                       help='Bump patch version (default)')
    parser.add_argument('--minor', action='store_true',
                       help='Bump minor version')
    parser.add_argument('--major', action='store_true',
                       help='Bump major version')
    parser.add_argument('--test-pypi', action='store_true',
                       help='Upload to TestPyPI instead of PyPI')
    parser.add_argument('--skip-tests', action='store_true',
                       help='Skip running tests')
    parser.add_argument('-m', '--message', type=str,
                       help='Custom commit message')
    parser.add_argument('--project-root', type=str,
                       help='Path to project root (default: current directory)')
    
    args = parser.parse_args()
    
    # Determine bump type
    if args.major:
        bump_type = 'major'
    elif args.minor:
        bump_type = 'minor'
    else:
        bump_type = 'patch'
    
    # Create deployer and run
    deployer = AutoDeploy(args.project_root)
    
    success = deployer.full_deploy(
        bump_type=bump_type,
        test_pypi=args.test_pypi,
        skip_tests=args.skip_tests,
        commit_message=args.message
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
