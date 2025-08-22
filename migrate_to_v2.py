#!/usr/bin/env python3
"""
Migration script for DumprX v1.x to v2.0.

This script helps users migrate their existing DumprX v1.x setup to the new Python-based v2.0.
"""

import shutil
import sys
from pathlib import Path

def print_banner():
    """Print migration banner."""
    banner = """
    🔄 DumprX Migration Tool
    ========================
    
    This tool helps you migrate from DumprX v1.x (Bash) to v2.0 (Python)
    """
    print(banner)

def check_v1_installation():
    """Check if v1.x installation exists."""
    v1_indicators = [
        'dumper.sh',
        'setup.sh', 
        'utils/unpackboot.sh'
    ]
    
    found_v1 = []
    for indicator in v1_indicators:
        if Path(indicator).exists():
            found_v1.append(indicator)
    
    return found_v1

def migrate_configuration():
    """Migrate configuration files from v1 to v2."""
    print("🔧 Migrating configuration files...")
    
    # Token files that can be reused
    token_files = [
        '.github_token',
        '.gitlab_token', 
        '.gitlab_group',
        '.tg_token',
        '.tg_chat'
    ]
    
    migrated = []
    for token_file in token_files:
        if Path(token_file).exists():
            print(f"  ✅ Found {token_file} - keeping for v2.0")
            migrated.append(token_file)
    
    if migrated:
        print(f"  🎉 Migrated {len(migrated)} configuration files")
    else:
        print("  ℹ️  No configuration files found to migrate")
    
    return migrated

def backup_v1_scripts():
    """Backup v1 scripts to a legacy directory."""
    print("📦 Backing up v1.x scripts...")
    
    backup_dir = Path("legacy_v1")
    backup_dir.mkdir(exist_ok=True)
    
    v1_scripts = [
        'dumper.sh',
        'setup.sh',
        'validate-workflow.sh'
    ]
    
    backed_up = []
    for script in v1_scripts:
        script_path = Path(script)
        if script_path.exists():
            backup_path = backup_dir / script
            shutil.copy2(script_path, backup_path)
            backed_up.append(script)
            print(f"  ✅ Backed up {script} to {backup_path}")
    
    if backed_up:
        print(f"  🎉 Backed up {len(backed_up)} v1.x scripts to legacy_v1/")
    
    return backed_up

def setup_v2_environment():
    """Set up v2.0 environment."""
    print("🚀 Setting up DumprX v2.0 environment...")
    
    # Check if v2 files exist
    v2_files = [
        'dumprx',
        'pyproject.toml',
        'src/dumprx'
    ]
    
    missing_v2 = []
    for v2_file in v2_files:
        if not Path(v2_file).exists():
            missing_v2.append(v2_file)
    
    if missing_v2:
        print(f"  ❌ Missing v2.0 files: {missing_v2}")
        print("  ⚠️  Please ensure you're running this script in the DumprX v2.0 directory")
        return False
    
    print("  ✅ All v2.0 files present")
    
    # Make dumprx executable
    dumprx_script = Path('dumprx')
    dumprx_script.chmod(dumprx_script.stat().st_mode | 0o755)
    print("  ✅ Made dumprx script executable")
    
    # Test v2 functionality
    try:
        import subprocess
        result = subprocess.run(['./dumprx', '--help'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("  ✅ DumprX v2.0 CLI is working")
        else:
            print(f"  ❌ DumprX v2.0 CLI test failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ Error testing v2.0 CLI: {e}")
        return False
    
    return True

def create_migration_summary():
    """Create a migration summary file."""
    summary_file = Path("MIGRATION_SUMMARY.md")
    
    summary_content = """# DumprX v1.x to v2.0 Migration Summary

## Migration Completed Successfully! 🎉

### What Changed
- **Scripts**: Bash scripts have been replaced with a unified Python CLI
- **Command**: Use `./dumprx` instead of `./dumper.sh`
- **Interface**: Modern CLI with rich output and better error messages

### New Commands
- `./dumprx extract <firmware>` - Main extraction command (replaces dumper.sh)
- `./dumprx test <firmware>` - Test extraction without upload/notification
- `./dumprx formats` - List supported formats
- `./dumprx vendors` - List supported vendors
- `./dumprx info <file>` - Get file information
- `./dumprx setup-telegram` - Configure Telegram bot
- `./dumprx setup-git` - Configure Git integration

### Configuration
- All your tokens and settings have been preserved
- Configuration is now managed via `dumprx_config.yaml`
- Same token files (.tg_token, .github_token, etc.) are used

### Quick Start with v2.0
```bash
# Test the new CLI
./dumprx --help

# Extract firmware (replaces ./dumper.sh firmware.zip)
./dumprx extract firmware.zip

# Test extraction without upload
./dumprx test firmware.zip

# Check configuration
./dumprx config-info
```

### Legacy Files
- v1.x bash scripts have been backed up to `legacy_v1/` directory
- They can be removed once you're satisfied with v2.0
- All functionality from v1.x is available in v2.0

### Need Help?
- Run `./dumprx help-command` for comprehensive usage guide
- Run `./dumprx <command> --help` for specific command help
- Check the README_v2.md for detailed documentation

---
**Migration completed on:** {date}
**DumprX version:** 2.0.0
"""
    
    from datetime import datetime
    summary_content = summary_content.format(date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    summary_file.write_text(summary_content)
    print(f"📋 Created migration summary: {summary_file}")

def main():
    """Main migration function."""
    print_banner()
    
    # Check current directory
    if not Path('dumprx').exists():
        print("❌ This doesn't appear to be a DumprX directory.")
        print("   Please run this script from the DumprX project root.")
        sys.exit(1)
    
    # Check for v1 installation
    v1_files = check_v1_installation()
    if not v1_files:
        print("ℹ️  No v1.x installation detected.")
        print("   This appears to be a fresh v2.0 installation.")
        
        # Still set up v2 environment
        if setup_v2_environment():
            print("\n🎉 DumprX v2.0 is ready to use!")
            print("   Run './dumprx --help' to get started.")
        else:
            print("\n❌ Failed to set up v2.0 environment.")
            sys.exit(1)
        return
    
    print(f"✅ Found v1.x installation with files: {v1_files}")
    
    # Migrate configuration
    migrated_config = migrate_configuration()
    
    # Backup v1 scripts
    backed_up = backup_v1_scripts()
    
    # Set up v2 environment
    if not setup_v2_environment():
        print("\n❌ Failed to set up v2.0 environment.")
        sys.exit(1)
    
    # Create migration summary
    create_migration_summary()
    
    print("\n" + "="*50)
    print("🎉 Migration completed successfully!")
    print("\n📋 Summary:")
    print(f"  • Configuration files migrated: {len(migrated_config)}")
    print(f"  • v1.x scripts backed up: {len(backed_up)}")
    print("  • v2.0 environment ready")
    
    print("\n🚀 Next steps:")
    print("  1. Test v2.0: ./dumprx --help")
    print("  2. Try extraction: ./dumprx test <firmware_file>")
    print("  3. Read MIGRATION_SUMMARY.md for details")
    print("  4. Remove legacy_v1/ when satisfied with v2.0")
    
    print("\n✨ Welcome to DumprX v2.0!")

if __name__ == "__main__":
    main()