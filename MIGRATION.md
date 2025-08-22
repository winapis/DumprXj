# Migration Guide: DumprX v1.x to v2.0.0

This guide helps you migrate from the bash-based DumprX v1.x to the new Python-based v2.0.0.

## What's Changed

### ✅ **Improvements in v2.0.0**
- **Modern Python CLI** - Better error handling, progress bars, rich output
- **Modular Architecture** - Easier to maintain and extend
- **Enhanced Configuration** - YAML config with backward compatibility
- **Better Download Support** - Improved handling of all sources
- **Advanced Git Integration** - Automatic repository creation and management
- **Professional Telegram Bot** - Rich HTML notifications
- **Cross-Platform Support** - Works on Linux, macOS, and Windows (WSL)

### 🔄 **Command Equivalents**

| v1.x (bash) | v2.0.0 (Python) | Notes |
|-------------|------------------|-------|
| `./dumper.sh firmware.zip` | `dumprx dump firmware.zip` | Main extraction command |
| `./dumper.sh 'https://mega.nz/...'` | `dumprx dump 'https://mega.nz/...'` | URL extraction |
| `./setup.sh` | `python3 setup.py` or `dumprx setup` | Dependency installation |
| N/A | `dumprx download URL` | Download without extraction |
| N/A | `dumprx config show` | View configuration |
| N/A | `dumprx test` | Test integrations |

### 📁 **File Structure Changes**

| Component | v1.x Location | v2.0.0 Location | Status |
|-----------|---------------|-----------------|--------|
| Main script | `dumper.sh` | `dumprx/cli.py` | ✅ Migrated |
| Setup script | `setup.sh` | `setup.py` | ✅ Migrated |
| Download scripts | `utils/downloaders/` | `dumprx/downloaders/` | ✅ Migrated |
| Extraction tools | Various utils | `dumprx/extractors/` | ✅ Migrated |
| Configuration | Token files | `config.yaml` + token files | ✅ Compatible |

### 🔧 **Configuration Migration**

#### Token Files (Still Supported)
Your existing token files will continue to work:
```bash
.github_token      # GitHub token
.github_orgname    # GitHub organization  
.gitlab_token      # GitLab token
.gitlab_group      # GitLab group
.gitlab_instance   # GitLab instance
.tg_token         # Telegram bot token
.tg_chat          # Telegram chat ID
```

#### New YAML Configuration (Optional)
You can now use a `config.yaml` file for centralized configuration:
```yaml
git:
  github:
    token: "your_github_token"
    organization: "your_org"
  gitlab:
    token: "your_gitlab_token"
    group: "your_group"

telegram:
  token: "your_telegram_token"
  chat_id: "@your_channel"
```

## Migration Steps

### 1. **Backup Current Setup**
```bash
# Backup your token files
cp .github_token .github_token.backup 2>/dev/null
cp .gitlab_token .gitlab_token.backup 2>/dev/null
cp .tg_token .tg_token.backup 2>/dev/null
# ... backup other token files

# Backup any custom configurations
cp -r utils/custom utils/custom.backup 2>/dev/null
```

### 2. **Install v2.0.0**
```bash
# Install Python dependencies
python3 setup.py

# Or manually
pip install -e .
```

### 3. **Test Installation**
```bash
# Check version
dumprx version

# Test configuration
dumprx config show

# Test integrations (if configured)
dumprx test
```

### 4. **Verify Functionality**
```bash
# Test with a simple archive
dumprx dump test_firmware.zip

# Test download (if needed)
dumprx download https://example.com/firmware.zip
```

### 5. **Update Workflows**
If you're using GitHub Actions, update your workflow files:

**Old (v1.x):**
```yaml
- name: Run dumper
  run: ./dumper.sh '${{ inputs.firmware_url }}'
```

**New (v2.0.0):**
```yaml
- name: Install DumprX
  run: pip install -e .

- name: Run dumper  
  run: dumprx dump '${{ inputs.firmware_url }}'
```

## Compatibility Matrix

### ✅ **Fully Compatible**
- All firmware types and formats
- All download sources (Mega, MediaFire, Google Drive, etc.)
- GitHub and GitLab integration
- Telegram notifications
- Token file authentication
- Output directory structure
- GitHub Actions workflow inputs

### ⚠️ **Requires Update**
- Custom bash scripts that call `dumper.sh` directly
- Hard-coded paths to bash scripts
- Custom extraction tools that depend on bash utilities

### ❌ **No Longer Supported**
- Direct bash script execution
- Bash-specific environment variables
- Custom bash functions

## Troubleshooting

### Common Migration Issues

**1. Command not found: dumprx**
```bash
# Solution: Reinstall the package
pip install -e .

# Or use full path
python3 -m dumprx.cli --help
```

**2. Permission denied errors**
```bash
# Solution: Fix permissions
sudo chown -R $USER:$USER .
chmod +x setup.py
```

**3. Missing dependencies**
```bash
# Solution: Run setup again
python3 setup.py

# Or install manually
sudo apt-get install python3 python3-pip git git-lfs
```

**4. Git integration not working**
```bash
# Solution: Check credentials and test
dumprx test

# Verify token permissions
# GitHub: needs 'repo' and 'user' scopes
# GitLab: needs 'api', 'read_user', 'write_repository' scopes
```

**5. Telegram notifications not working**
```bash
# Solution: Test bot connection
dumprx test

# Verify bot token and chat ID
dumprx config show
```

### Performance Comparison

| Operation | v1.x (bash) | v2.0.0 (Python) | Improvement |
|-----------|-------------|------------------|-------------|
| Download speed | Good | Better | Progress bars, resume support |
| Extraction speed | Good | Similar | Better error handling |
| Error reporting | Basic | Rich | Detailed messages, colors |
| Progress tracking | Limited | Excellent | Real-time progress bars |
| Memory usage | Variable | Optimized | Better handling of large files |

## Rollback Plan

If you need to rollback to v1.x temporarily:

### 1. **Keep Old Scripts**
The old bash scripts are preserved in the repository for compatibility.

### 2. **Switch Commands**
```bash
# Use old bash scripts
./dumper.sh firmware.zip

# Use new Python CLI
dumprx dump firmware.zip
```

### 3. **Restore Backups**
```bash
# Restore token files if needed
cp .github_token.backup .github_token
```

## Getting Help

### Resources
- **Documentation**: Check the new README_v2.md
- **Examples**: Use `dumprx --help` for command examples
- **Issues**: Report problems on GitHub Issues
- **Configuration**: Use `dumprx config show` to debug settings

### Community Support
- **GitHub Discussions**: For questions and help
- **Issues**: For bugs and feature requests
- **Wiki**: For detailed documentation and guides

## Success Checklist

After migration, verify these work:

- [ ] `dumprx version` shows v2.0.0
- [ ] `dumprx config show` displays your settings
- [ ] `dumprx test` passes (if integrations configured)
- [ ] Firmware extraction works: `dumprx dump test_file.zip`
- [ ] Downloads work: `dumprx download test_url`
- [ ] Git integration works (if configured)
- [ ] Telegram notifications work (if configured)
- [ ] GitHub Actions workflow updated and tested

---

**Welcome to DumprX v2.0.0!** 🚀

The migration brings significant improvements while maintaining full compatibility with your existing setup. If you encounter any issues, please check the troubleshooting section or open an issue on GitHub.