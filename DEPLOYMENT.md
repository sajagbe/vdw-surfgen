# Automated Deployment Guide

This project includes several automated deployment tools to streamline the process of releasing new versions to GitHub and PyPI.

## 🚀 Quick Start

### Option 1: Simple Deployment (Recommended)
```bash
./deploy.sh                 # Patch version bump and deploy
./deploy.sh --minor         # Minor version bump
./deploy.sh --major         # Major version bump
./deploy.sh --test-pypi     # Deploy to TestPyPI first
```

### Option 2: Direct Python Script
```bash
python auto_deploy.py                    # Patch version bump and deploy
python auto_deploy.py --minor            # Minor version bump
python auto_deploy.py --major            # Major version bump
python auto_deploy.py --test-pypi        # Deploy to TestPyPI first
python auto_deploy.py --skip-tests       # Skip running tests
python auto_deploy.py -m "Custom commit message"
```

## 📁 Files Overview

### `auto_deploy.py`
The main automation script that handles:
- ✅ Version bumping (patch/minor/major)
- 🧪 Running tests (if they exist)
- 📦 Building the package
- 🔄 Committing and pushing to GitHub
- 🚀 Uploading to PyPI/TestPyPI

### `deploy.sh`
A simple bash wrapper that:
- 📦 Installs deployment dependencies
- 🚀 Runs the Python deployment script

### `deploy_requirements.txt`
Dependencies needed for deployment:
- `colorama` - Colored terminal output
- `build` - Modern Python package building
- `twine` - PyPI upload tool
- `wheel` - Wheel format support

### `.git/hooks/pre-commit`
Git hook that can automatically trigger deployment on commits.

### `.github/workflows/auto-deploy.yml`
GitHub Actions workflow for automated CI/CD deployment.

## 🛠️ Setup Instructions

### 1. PyPI Authentication
You need to set up PyPI authentication. Choose one method:

#### Method A: API Token (Recommended)
1. Go to https://pypi.org/manage/account/
2. Create an API token
3. Store it in `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-your-api-token-here
```

#### Method B: Environment Variables
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-api-token-here
```

### 2. GitHub Authentication
Make sure you can push to your GitHub repository:
```bash
git remote -v  # Check your remote
git push origin main  # Test push access
```

### 3. Install Dependencies
```bash
pip install -r deploy_requirements.txt
```

## 🔧 Advanced Usage

### Enable Auto-Deploy on Commit
```bash
# Enable auto-deploy with patch version bumps
echo "patch" > .auto-deploy

# Enable auto-deploy with minor version bumps
echo "minor" > .auto-deploy

# Disable auto-deploy
rm .auto-deploy
```

### Test Before Production
Always test with TestPyPI first:
```bash
./deploy.sh --test-pypi
```

### Custom Commit Messages
```bash
python auto_deploy.py -m "🐛 Fix critical bug in surface generation"
```

### Skip Tests (if needed)
```bash
python auto_deploy.py --skip-tests
```

## 📊 What the Script Does

1. **🔍 Pre-checks**: Installs dependencies, checks git status
2. **🧪 Testing**: Runs any test files found (test*.py)
3. **📈 Version Bump**: Increments version in pyproject.toml/setup.py
4. **📦 Building**: Creates source and wheel distributions
5. **✅ Validation**: Checks package integrity with twine
6. **📤 GitHub**: Commits changes, creates tags, pushes to GitHub
7. **🚀 PyPI**: Uploads package to PyPI or TestPyPI
8. **🎉 Success**: Reports deployment status

## 🔍 Monitoring

### Check Deployment Status
```bash
# View deployment log
cat auto_deploy.log

# Check git status
git status

# Check latest tag
git tag -l | tail -5

# Check PyPI package
pip search vdw-surfgen  # or visit https://pypi.org/project/vdw-surfgen/
```

### GitHub Actions
Monitor deployments at: `https://github.com/yourusername/vdw-surfgen/actions`

## 🚨 Troubleshooting

### Common Issues

#### 1. Version Already Exists on PyPI
```bash
# Force a new version bump
python auto_deploy.py --patch  # or --minor/--major
```

#### 2. Authentication Failed
```bash
# Check your PyPI credentials
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
```

#### 3. Git Push Failed
```bash
# Check remote and credentials
git remote -v
git push origin main
```

#### 4. Build Failed
```bash
# Clean and retry
rm -rf build dist *.egg-info
python auto_deploy.py
```

### Debug Mode
Add `--verbose` to see detailed output:
```bash
python auto_deploy.py --verbose
```

## 🔄 Workflow Examples

### Daily Development
```bash
# Make your changes
git add .
git commit -m "Add new feature"

# Quick patch release
./deploy.sh
```

### Feature Release
```bash
# Major feature completed
./deploy.sh --minor
```

### Breaking Changes
```bash
# API breaking changes
./deploy.sh --major
```

### Safe Testing
```bash
# Test on TestPyPI first
./deploy.sh --test-pypi

# If successful, deploy to production
./deploy.sh
```

## 📋 Checklist Before First Use

- [ ] PyPI account created and API token configured
- [ ] GitHub repository access confirmed
- [ ] Dependencies installed (`pip install -r deploy_requirements.txt`)
- [ ] Test deployment to TestPyPI successful
- [ ] All tests passing
- [ ] README and documentation updated

## 🎯 Best Practices

1. **Always test first**: Use `--test-pypi` for new features
2. **Semantic versioning**: Use patch/minor/major appropriately
3. **Clean commits**: Make meaningful commit messages
4. **Run tests**: Ensure code quality before deployment
5. **Monitor releases**: Check PyPI and GitHub after deployment
6. **Backup**: Keep local backups of important versions

---

**Happy Deploying! 🚀**
